import socket
import sqlite3
import uuid
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.db import fetch_one_dict, init_sqlite_db, sqlite_conn, upsert_printer_by_code
from app.models.printer import Printer
from app.schemas.printer import PrinterCreate, PrinterDiscoveryResult


class PrinterService:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=10)
        init_sqlite_db()
        self.seed_from_yaml(only_if_empty=True)

    def seed_from_yaml(self, *, only_if_empty: bool = False) -> dict[str, int]:
        config_path = settings.printers_config_path
        if not config_path.exists():
            return {"inserted": 0, "updated": 0}

        with sqlite_conn() as conn:
            if only_if_empty:
                existing_count = conn.execute("SELECT COUNT(1) FROM printers").fetchone()[0]
                if existing_count and int(existing_count) > 0:
                    return {"inserted": 0, "updated": 0}

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except Exception:
            return {"inserted": 0, "updated": 0}

        printers = (config or {}).get("printers") or []
        inserted = 0
        updated = 0

        for p in printers:
            name = p.get("name")
            host = p.get("host")
            if not name or not host:
                continue
            port = int(p.get("port") or settings.default_printer_port)
            printer_code = p.get("printer_code")
            if printer_code:
                with sqlite_conn() as conn:
                    existing = conn.execute(
                        "SELECT id FROM printers WHERE printer_code = ?",
                        (printer_code,),
                    ).fetchone()
                pid = existing["id"] if existing else str(uuid.uuid4())
                before_exists = bool(existing)
                upsert_printer_by_code(
                    printer_code=str(printer_code),
                    name=str(name),
                    host=str(host),
                    port=port,
                    printer_id=str(pid),
                )
                updated += 1 if before_exists else 0
                inserted += 0 if before_exists else 1
                continue

            printer_id = str(uuid.uuid4())
            with sqlite_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO printers (id, name, printer_code, host, port, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    (printer_id, str(name), None, str(host), port),
                )
            inserted += 1

        return {"inserted": inserted, "updated": updated}

    def register(self, data: PrinterCreate) -> Printer:
        printer_id = str(uuid.uuid4())
        try:
            with sqlite_conn() as conn:
                conn.execute(
                    """
                    INSERT INTO printers (id, name, printer_code, host, port, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    (printer_id, data.name, data.printer_code, data.host, data.port),
                )
        except sqlite3.IntegrityError as e:
            raise ValueError(str(e))
        return Printer(
            id=printer_id,
            name=data.name,
            printer_code=data.printer_code,
            host=data.host,
            port=data.port,
        )

    def get(self, printer_id: str) -> Optional[Printer]:
        with sqlite_conn() as conn:
            row = fetch_one_dict(conn, "SELECT * FROM printers WHERE id = ?", (printer_id,))
        if not row:
            return None
        printer = Printer(
            id=row["id"],
            name=row["name"],
            printer_code=row.get("printer_code"),
            host=row["host"],
            port=int(row["port"]),
        )
        printer.is_available = self.check_reachable(printer.host, printer.port)
        return printer

    def get_by_code(self, printer_code: str) -> Optional[Printer]:
        """Get a printer by its printer_code."""
        with sqlite_conn() as conn:
            row = fetch_one_dict(conn, "SELECT * FROM printers WHERE printer_code = ?", (printer_code,))
        if not row:
            return None
        printer = Printer(
            id=row["id"],
            name=row["name"],
            printer_code=row.get("printer_code"),
            host=row["host"],
            port=int(row["port"]),
        )
        printer.is_available = self.check_reachable(printer.host, printer.port)
        return printer

    def list_all(self) -> list[Printer]:
        with sqlite_conn() as conn:
            rows = conn.execute("SELECT * FROM printers ORDER BY name ASC").fetchall()
        printers = [
            Printer(
                id=str(r["id"]),
                name=str(r["name"]),
                printer_code=r["printer_code"],
                host=str(r["host"]),
                port=int(r["port"]),
            )
            for r in rows
        ]
        futures = {self._executor.submit(self.check_reachable, p.host, p.port): p for p in printers}
        for future in as_completed(futures):
            p = futures[future]
            try:
                p.is_available = bool(future.result())
            except Exception:
                p.is_available = False
        return printers

    def delete(self, printer_id: str) -> bool:
        with sqlite_conn() as conn:
            cur = conn.execute("DELETE FROM printers WHERE id = ?", (printer_id,))
            return bool(cur.rowcount and cur.rowcount > 0)

    def update(
        self,
        printer_id: str,
        *,
        name: Optional[str] = None,
        printer_code: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ) -> Optional[Printer]:
        fields: list[tuple[str, object]] = []
        if name is not None:
            fields.append(("name", name))
        if printer_code is not None:
            fields.append(("printer_code", printer_code))
        if host is not None:
            fields.append(("host", host))
        if port is not None:
            fields.append(("port", int(port)))

        if not fields:
            return self.get(printer_id)

        set_clause = ", ".join([f"{k} = ?" for k, _ in fields] + ["updated_at = datetime('now')"])
        params = tuple([v for _, v in fields] + [printer_id])
        try:
            with sqlite_conn() as conn:
                cur = conn.execute(f"UPDATE printers SET {set_clause} WHERE id = ?", params)
                if not cur.rowcount:
                    return None
        except sqlite3.IntegrityError as e:
            raise ValueError(str(e))
        return self.get(printer_id)

    def check_reachable(self, host: str, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(settings.discovery_timeout_seconds)
                sock.connect((host, port))
                return True
        except (socket.timeout, socket.error, OSError):
            return False

    def discover_on_network(self, network_prefix: str = "192.168.1", port: int = 9100) -> list[PrinterDiscoveryResult]:
        """Scan a /24 subnet for devices with the given port open (e.g. 9100 for raw printing)."""
        results: list[PrinterDiscoveryResult] = []
        base = network_prefix.rsplit(".", 1)[0]

        def check_host(ip: str) -> PrinterDiscoveryResult:
            reachable = self.check_reachable(ip, port)
            return PrinterDiscoveryResult(host=ip, port=port, reachable=reachable)

        futures = {}
        for i in range(1, 255):
            ip = f"{base}.{i}"
            futures[self._executor.submit(check_host, ip)] = ip

        for future in as_completed(futures, timeout=30):
            try:
                result = future.result()
                if result.reachable:
                    results.append(result)
            except Exception:
                pass

        return results


# Singleton for the app
printer_service = PrinterService()
