from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    app_name: str = "Printer API"
    templates_dir: Path = Path(__file__).resolve().parent.parent / "templates"
    # Path to printers YAML configuration file
    printers_config_path: Path = Path(__file__).resolve().parent.parent.parent / "printers.yaml"
    # Default port for raw printing (many thermal printers)
    default_printer_port: int = 9100
    # Discovery: timeout in seconds when scanning for printers
    discovery_timeout_seconds: float = 1.0
    # Width of the receipt text grid in printer dots: 40 template columns x the
    # 12-dot Font A. Centred images are padded to this width so they share a
    # centre line with centred text; centring on the paper instead (576 dots on
    # 80mm stock) would push them 48 dots right of the 40-column layout.
    receipt_width_dots: int = 480

    sqlite_db_path: Path = Path(__file__).resolve().parent.parent.parent / "printers.sqlite3"

    # Failure log: one JSON object per line, rotated when it grows too large
    print_log_path: Path = (
        Path(__file__).resolve().parent.parent.parent / "logs" / "print_failures.log"
    )
    print_log_max_bytes: int = 5 * 1024 * 1024
    print_log_backup_count: int = 5
    print_log_include_metadata: bool = True

    # Error log: every request that ends in a 4xx/5xx, one JSON object per line
    # with the traceback and HTTP payload. Written off the event loop.
    error_log_path: Path = (
        Path(__file__).resolve().parent.parent.parent / "logs" / "errors.log"
    )
    error_log_max_bytes: int = 5 * 1024 * 1024
    error_log_backup_count: int = 5
    # Request body bytes kept per entry; 0 disables body capture.
    error_log_max_body_bytes: int = 16 * 1024

    # --- Print dispatch ---
    # Jobs accepted per printer per sliding window. A thermal printer needs
    # roughly 0.5-1s per receipt, so this is a burst ceiling rather than a
    # sustained throughput target -- the serialized per-printer worker is what
    # actually paces delivery.
    print_rate_limit: int = 4
    print_rate_window_seconds: float = 1.0
    # How long a caller waits for its receipt before getting 503 + Retry-After.
    print_wait_timeout_seconds: float = 5.0
    # Backlog per printer before the API sheds load with a 503.
    # Keep this at roughly print_rate_limit * print_wait_timeout_seconds. A
    # deeper queue does not buy throughput: a job queued behind more than that
    # cannot be reached before its caller's wait budget expires, so it would be
    # abandoned anyway -- and rejecting it on arrival returns the 503 in
    # milliseconds instead of making the POS wait the full timeout first.
    print_max_queue_depth: int = 20
    # Socket timeouts. A printer on the LAN answers in milliseconds; the old
    # 10s connect timeout only served to pin a thread to a dead printer.
    print_connect_timeout_seconds: float = 3.0
    print_send_timeout_seconds: float = 5.0
    print_retry_delay_seconds: float = 0.5
    print_max_attempts: int = 2

    # CORS Configuration - Configure in code, not via environment variables
    cors_origins: List[str] = ["*"]  # Allow all origins by default
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    class Config:
        env_prefix = "PRINTER_"
        # Exclude CORS settings from environment variable parsing
        fields = {
            'cors_origins': {'exclude': True},
            'cors_credentials': {'exclude': True},
            'cors_methods': {'exclude': True},
            'cors_headers': {'exclude': True},
        }


settings = Settings()
