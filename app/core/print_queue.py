"""Per-printer job dispatch.

An ESC/POS printer on port 9100 accepts one TCP connection at a time, so jobs
destined for a single printer must be delivered strictly one after another.
Concurrency is therefore *across* printers, never within one: each printer gets
its own bounded queue and exactly one worker task draining it.

That single worker is what makes delivery safe. The sliding-window limiter on
top of it paces the worker so a burst cannot outrun the paper feed, and the
bounded queue is what turns overload into a fast, explicit 503 instead of a
socket read timeout on the caller.

The blocking socket write runs in a worker thread so the event loop stays free
to accept and reply to requests while paper is moving.
"""

from __future__ import annotations

import asyncio
import enum
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

import anyio.to_thread

from app.core.ratelimit import InMemorySlidingWindowLimiter, RateLimiter


class QueueFullError(Exception):
    """The printer's backlog is at capacity; shed load (maps to HTTP 503)."""


class JobState(enum.Enum):
    QUEUED = "queued"
    SENDING = "sending"
    DONE = "done"
    ABANDONED = "abandoned"


@dataclass
class PrintJob:
    job_id: str
    printer_key: str
    send: Callable[[], bool]
    enqueued_at: float = field(default_factory=time.monotonic)
    state: JobState = JobState.QUEUED
    future: asyncio.Future = field(default_factory=asyncio.Future)

    def try_start(self) -> bool:
        """Claim the job for sending. False if the caller already abandoned it."""
        if self.state is not JobState.QUEUED:
            return False
        self.state = JobState.SENDING
        return True

    def try_abandon(self) -> bool:
        """Drop the job if it has not started yet.

        Returns True when the job is guaranteed not to reach the printer, which
        is what lets the API answer "not printed" without lying. Once the state
        is SENDING the bytes may already be on the wire, so the caller must wait
        for the real outcome instead.
        """
        if self.state is not JobState.QUEUED:
            return False
        self.state = JobState.ABANDONED
        return True


class PrintDispatcher:
    """Routes jobs to one serialized, rate-paced worker per printer."""

    def __init__(
        self,
        *,
        limiter: Optional[RateLimiter] = None,
        rate_limit: int = 4,
        window_seconds: float = 1.0,
        max_queue_depth: int = 50,
    ) -> None:
        self._limiter = limiter or InMemorySlidingWindowLimiter(
            limit=rate_limit, window_seconds=window_seconds
        )
        self._max_queue_depth = max_queue_depth
        self._queues: Dict[str, asyncio.Queue] = {}
        self._workers: Dict[str, asyncio.Task] = {}
        self._closed = False

    def _queue_for(self, printer_key: str) -> asyncio.Queue:
        queue = self._queues.get(printer_key)
        if queue is None:
            queue = asyncio.Queue(maxsize=self._max_queue_depth)
            self._queues[printer_key] = queue
            self._workers[printer_key] = asyncio.create_task(
                self._worker(printer_key, queue),
                name=f"print-worker:{printer_key}",
            )
        return queue

    async def submit(self, job: PrintJob) -> PrintJob:
        """Enqueue *job*. Raises :class:`QueueFullError` when the backlog is full."""
        if self._closed:
            raise QueueFullError("Print dispatcher is shutting down.")
        queue = self._queue_for(job.printer_key)
        try:
            queue.put_nowait(job)
        except asyncio.QueueFull:
            raise QueueFullError(
                f"Printer {job.printer_key} has {queue.qsize()} jobs queued "
                f"(max {self._max_queue_depth})."
            )
        return job

    async def _worker(self, printer_key: str, queue: asyncio.Queue) -> None:
        while True:
            job = await queue.get()
            try:
                if not job.try_start():
                    continue  # caller gave up before we reached it
                await self._limiter.acquire(printer_key)
                try:
                    ok = await anyio.to_thread.run_sync(job.send)
                    if not job.future.done():
                        job.future.set_result(bool(ok))
                except BaseException as exc:  # noqa: BLE001 - surfaced to caller
                    if not job.future.done():
                        job.future.set_exception(exc)
                        # The caller may have already walked away (disconnect or
                        # abandoned wait); consume it so asyncio does not log
                        # "exception was never retrieved" for a handled failure.
                        job.future.add_done_callback(lambda f: f.exception())
                finally:
                    job.state = JobState.DONE
            finally:
                queue.task_done()

    def depth(self, printer_key: str) -> int:
        queue = self._queues.get(printer_key)
        return queue.qsize() if queue else 0

    def stats(self) -> dict:
        return {
            key: {"queued": queue.qsize(), "max_depth": self._max_queue_depth}
            for key, queue in self._queues.items()
        }

    async def aclose(self) -> None:
        """Stop accepting work and cancel the workers."""
        self._closed = True
        for task in self._workers.values():
            task.cancel()
        for task in self._workers.values():
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        self._workers.clear()
        self._queues.clear()


dispatcher: Optional[PrintDispatcher] = None


def build_dispatcher() -> PrintDispatcher:
    """Construct a dispatcher from settings. Must be called inside the loop."""
    from app.core.config import settings

    return PrintDispatcher(
        rate_limit=settings.print_rate_limit,
        window_seconds=settings.print_rate_window_seconds,
        max_queue_depth=settings.print_max_queue_depth,
    )


def get_dispatcher() -> PrintDispatcher:
    """Return the process dispatcher, creating it on first use.

    Normally the lifespan handler builds it at startup and closes it on
    shutdown. Falling back to lazy creation keeps the print path working for
    callers that mount the app without running lifespan (notably a bare
    ``TestClient(app)``), rather than failing every print with a 500.
    """
    global dispatcher
    if dispatcher is None:
        dispatcher = build_dispatcher()
    return dispatcher
