"""Deferred JSON Lines error log for HTTP requests.

Every request that ends in an error -- an HTTPException, a request validation
failure, or an unhandled exception -- is written as one compact JSON object
carrying the traceback and the HTTP payload that triggered it (method, path,
query, headers, body).

Logging is deferred: the exception handlers only format the record and push it
onto an in-memory queue, and a QueueListener thread does the file and stderr
I/O, so a slow disk never stalls the event loop. Records logged before
``start()`` are buffered and written once the listener is running. Like the
print failure log, nothing in here is allowed to raise into the request path.
"""

import json
import logging
import queue
import sys
from datetime import datetime, timezone, timedelta
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings


_TZ_UTC_PLUS_7 = timezone(timedelta(hours=7))

# Attributes every LogRecord has. Anything else arrived through ``extra=`` and
# is emitted as a top-level JSON field.
_RESERVED_ATTRS = frozenset(vars(logging.makeLogRecord({}))) | {"message", "asctime"}

_REDACTED_HEADERS = frozenset(
    {"authorization", "proxy-authorization", "cookie", "set-cookie", "x-api-key"}
)

_BODY_STATE_KEY = "error_log_body"


class JsonFormatter(logging.Formatter):
    """Render a record as one compact JSON line, traceback included."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, _TZ_UTC_PLUS_7).isoformat(
                timespec="milliseconds"
            ),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": record.getMessage(),
        }
        entry.update((k, v) for k, v in vars(record).items() if k not in _RESERVED_ATTRS)

        if record.exc_info and record.exc_info[1] is not None:
            exc = record.exc_info[1]
            entry["error_class"] = type(exc).__name__
            entry["error"] = str(exc)
            entry["traceback"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str, ensure_ascii=False, separators=(",", ":"))


_queue: "queue.Queue[logging.LogRecord]" = queue.Queue()
_listener: Optional[QueueListener] = None

logger = logging.getLogger("printerapi.errors")
logger.setLevel(logging.WARNING)
logger.propagate = False
_queue_handler = QueueHandler(_queue)
# Formatting happens on the caller while exc_info is still attached;
# QueueHandler.prepare then drops the traceback object, so the listener thread
# only ever sees the finished JSON line.
_queue_handler.setFormatter(JsonFormatter())
logger.addHandler(_queue_handler)


def start() -> None:
    """Start the background writer thread. Safe to call more than once."""
    global _listener
    if _listener is not None:
        return

    # The record *is* the JSON line; no extra formatting.
    line = logging.Formatter("%(message)s")
    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(line)
    handlers: list[logging.Handler] = [stream]

    try:
        settings.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            str(settings.error_log_path),
            maxBytes=settings.error_log_max_bytes,
            backupCount=settings.error_log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(line)
        handlers.append(file_handler)
    except Exception as e:  # read-only FS, bad path, permissions...
        print(f"[WARN] Error log file disabled ({settings.error_log_path}): {e}")

    _listener = QueueListener(_queue, *handlers)
    _listener.start()


def stop() -> None:
    """Flush everything still queued, then stop the writer thread."""
    global _listener
    if _listener is None:
        return
    _listener.stop()
    for handler in _listener.handlers:
        handler.close()
    _listener = None


class _BodyTap:
    __slots__ = ("data", "size")

    def __init__(self) -> None:
        self.data = bytearray()
        self.size = 0


class RequestBodyTapMiddleware:
    """Keep a bounded copy of the request body for the error log.

    The body stream can be read only once, and the catch-all 500 handler is
    handed a Request with no receive channel, so the bytes are copied as the app
    reads them rather than re-read after the error.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        tap = _BodyTap()
        scope.setdefault("state", {})[_BODY_STATE_KEY] = tap

        async def tapped_receive() -> Message:
            message = await receive()
            if message["type"] == "http.request":
                chunk = message.get("body", b"")
                room = self.max_bytes - len(tap.data)
                if room > 0:
                    tap.data += chunk[:room]
                tap.size += len(chunk)
            return message

        await self.app(scope, tapped_receive, send)


def _decode_body(tap: _BodyTap) -> Any:
    raw = bytes(tap.data)
    if tap.size == len(raw):
        try:
            return json.loads(raw)
        except ValueError:
            pass
    return raw.decode("utf-8", errors="replace")


def _http_payload(request: Request) -> dict:
    payload: dict[str, Any] = {
        "method": request.method,
        "path": request.url.path,
        "query": request.url.query or None,
        "client": request.client.host if request.client else None,
        "headers": {
            k: "[REDACTED]" if k in _REDACTED_HEADERS else v
            for k, v in request.headers.items()
        },
    }

    tap = request.scope.get("state", {}).get(_BODY_STATE_KEY)
    if tap is not None and tap.size:
        payload["body"] = _decode_body(tap)
        payload["body_bytes"] = tap.size
        if tap.size > len(tap.data):
            payload["body_truncated"] = True
    return payload


def log_request_error(
    event: str,
    request: Request,
    exc: BaseException,
    *,
    status_code: int,
    **fields: Any,
) -> None:
    """Queue one JSON line for a request that failed with *exc*.

    5xx is logged at ERROR and 4xx at WARNING. Extra keyword arguments become
    top-level fields of the entry.
    """
    try:
        logger.log(
            logging.ERROR if status_code >= 500 else logging.WARNING,
            event,
            exc_info=exc,
            extra={"status_code": status_code, **fields, "http": _http_payload(request)},
        )
    except Exception as e:
        # Never let logging break the error response.
        print(f"[WARN] Failed to write error log entry: {e}")


async def _on_http_exception(request: Request, exc: StarletteHTTPException) -> Response:
    log_request_error(
        "http_error", request, exc, status_code=exc.status_code, detail=exc.detail
    )
    return await http_exception_handler(request, exc)


async def _on_validation_error(request: Request, exc: RequestValidationError) -> Response:
    log_request_error(
        "validation_error", request, exc, status_code=422, errors=exc.errors()
    )
    return await request_validation_exception_handler(request, exc)


async def _on_unhandled_exception(request: Request, exc: Exception) -> Response:
    log_request_error("unhandled_exception", request, exc, status_code=500)
    # Same response Starlette sends when no 500 handler is installed.
    return PlainTextResponse("Internal Server Error", status_code=500)


def install(app: FastAPI) -> None:
    """Attach the body tap and the error-logging exception handlers to *app*."""
    if settings.error_log_max_body_bytes > 0:
        app.add_middleware(
            RequestBodyTapMiddleware, max_bytes=settings.error_log_max_body_bytes
        )
    app.add_exception_handler(StarletteHTTPException, _on_http_exception)
    app.add_exception_handler(RequestValidationError, _on_validation_error)
    app.add_exception_handler(Exception, _on_unhandled_exception)
