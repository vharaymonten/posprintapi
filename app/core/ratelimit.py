"""Sliding-window rate limiting for print dispatch.

The limiter is defined as a small async interface so the storage backend can be
swapped without touching call sites. :class:`InMemorySlidingWindowLimiter` is the
default and is correct for a single API process, which is how this service is
deployed. If the API is ever scaled to several replicas that share the same
physical printers, add a Redis-backed implementation of :class:`RateLimiter`
(sorted-set per key, ``ZREMRANGEBYSCORE`` + ``ZCARD`` + ``ZADD`` in one Lua
script) and swap the instance built in :mod:`app.core.print_queue`.

Note that the limiter alone does not make printing safe: an ESC/POS printer
accepts a single TCP connection at a time, so jobs for one printer must also be
*serialized*. That is the dispatcher's job; this module only paces them.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Deque, Dict, Protocol


class RateLimiter(Protocol):
    """Paces work per key. Implementations must be safe for concurrent use."""

    async def acquire(self, key: str) -> float:
        """Block until a slot is free for *key*, then consume it.

        Returns the number of seconds spent waiting, for observability.
        """
        ...


class InMemorySlidingWindowLimiter:
    """Per-key sliding window over a deque of grant timestamps.

    Unlike a fixed window, this cannot pass 2x the limit across a boundary: a
    grant is only made when the number of grants in the trailing
    ``window_seconds`` is below ``limit``. Timestamps use a monotonic clock, so
    the window is immune to wall-clock adjustments (NTP steps, DST).
    """

    def __init__(self, limit: int, window_seconds: float = 1.0) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self._limit = limit
        self._window = float(window_seconds)
        self._grants: Dict[str, Deque[float]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    def _lock_for(self, key: str) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def acquire(self, key: str) -> float:
        started = time.monotonic()
        async with self._lock_for(key):
            grants = self._grants.setdefault(key, deque())
            while True:
                now = time.monotonic()
                cutoff = now - self._window
                while grants and grants[0] <= cutoff:
                    grants.popleft()

                if len(grants) < self._limit:
                    grants.append(now)
                    return time.monotonic() - started

                # Sleep until the oldest grant leaves the window, then re-check
                # rather than granting straight away -- the deque may have been
                # refilled while this task was suspended.
                await asyncio.sleep(max(0.0, grants[0] - cutoff))

    def snapshot(self, key: str) -> int:
        """Current in-window usage for *key*, for the health endpoint."""
        grants = self._grants.get(key)
        if not grants:
            return 0
        cutoff = time.monotonic() - self._window
        return sum(1 for g in grants if g > cutoff)
