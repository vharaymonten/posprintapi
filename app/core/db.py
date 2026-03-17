import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

from app.core.config import settings


def init_sqlite_db(db_path: Optional[Path] = None) -> None:
    path = db_path or settings.sqlite_db_path
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(path)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS printers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                printer_code TEXT UNIQUE,
                host TEXT NOT NULL,
                port INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_printers_host ON printers(host)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_printers_port ON printers(port)")
        conn.commit()


@contextmanager
def sqlite_conn(db_path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    path = db_path or settings.sqlite_db_path
    init_sqlite_db(path)

    conn = sqlite3.connect(str(path))
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


def upsert_printer_by_code(
    *,
    printer_code: str,
    name: str,
    host: str,
    port: int,
    printer_id: Optional[str] = None,
    db_path: Optional[Path] = None,
) -> str:
    with sqlite_conn(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM printers WHERE printer_code = ?",
            (printer_code,),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE printers
                SET name = ?, host = ?, port = ?, updated_at = datetime('now')
                WHERE printer_code = ?
                """,
                (name, host, port, printer_code),
            )
            return str(existing["id"])

        pid = printer_id
        if not pid:
            raise ValueError("printer_id is required for insert upsert path")
        conn.execute(
            """
            INSERT INTO printers (id, name, printer_code, host, port, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (pid, name, printer_code, host, port),
        )
        return pid


def fetch_one_dict(conn: sqlite3.Connection, query: str, params: tuple[Any, ...]) -> Optional[dict[str, Any]]:
    row = conn.execute(query, params).fetchone()
    return dict(row) if row else None
