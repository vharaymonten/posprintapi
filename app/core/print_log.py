"""JSON Lines failure log for print jobs.

Every failed print attempt appends one compact JSON object to
``settings.print_log_path`` so failures leave a durable trace instead of
vanishing with the process stdout. Logging is strictly best-effort: nothing in
here is allowed to raise into the print path.
"""

import json
import logging
import traceback
from datetime import datetime, timezone, timedelta
from logging.handlers import RotatingFileHandler
from typing import Any, Optional

from app.core.config import settings


_TZ_UTC_PLUS_7 = timezone(timedelta(hours=7))

_logger: Optional[logging.Logger] = None


def _get_logger() -> logging.Logger:
    """Return the singleton failure logger, creating its handler on first use."""
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("print_failures")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    try:
        settings.print_log_path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            str(settings.print_log_path),
            maxBytes=settings.print_log_max_bytes,
            backupCount=settings.print_log_backup_count,
            encoding="utf-8",
        )
        # The record *is* the JSON line; no extra formatting.
        handler.setFormatter(logging.Formatter("%(message)s"))
    except Exception as e:  # read-only FS, bad path, permissions...
        print(f"[WARN] Print failure log disabled ({settings.print_log_path}): {e}")
        handler = logging.NullHandler()

    logger.addHandler(handler)
    _logger = logger
    return logger


def _printer_fields(printer: Any) -> Optional[dict]:
    if printer is None:
        return None
    return {
        "id": getattr(printer, "id", None),
        "printer_code": getattr(printer, "printer_code", None),
        "name": getattr(printer, "name", None),
        "host": getattr(printer, "host", None),
        "port": getattr(printer, "port", None),
    }


def log_print_failure(
    event: str,
    error_type: str,
    *,
    job_id: Optional[str] = None,
    template_name: Optional[str] = None,
    printer: Any = None,
    metadata: Optional[dict] = None,
    exc: Optional[BaseException] = None,
    **extra: Any,
) -> None:
    """Append one JSON line describing a failed print job.

    *event* is the failure point (``printer_send_failed``, ``render_failed``,
    ``printer_not_found``, ``image_build_failed``) and *error_type* is either
    ``printer_failure`` or ``input_error``. Any extra keyword arguments are
    merged into the entry as-is.
    """
    try:
        entry = {
            "ts": datetime.now(_TZ_UTC_PLUS_7).isoformat(timespec="milliseconds"),
            "level": "error",
            "event": event,
            "error_type": error_type,
            "job_id": job_id,
            "template_name": template_name,
            "printer": _printer_fields(printer),
        }
        entry.update(extra)

        if exc is not None:
            entry["error"] = str(exc)
            entry["error_class"] = type(exc).__name__
            entry["traceback"] = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )

        if metadata is not None and settings.print_log_include_metadata:
            entry["metadata"] = metadata

        line = json.dumps(entry, default=str, ensure_ascii=False, separators=(",", ":"))
        _get_logger().error(line)
    except Exception as e:
        # Never let logging break printing.
        print(f"[WARN] Failed to write print failure log entry: {e}")
