import socket
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from app.core.config import settings
from app.models.printer import Printer
from app.schemas.printer import PrinterCreate, PrinterDiscoveryResult


class PrinterService:
    def __init__(self) -> None:
        self._printers: dict[str, Printer] = {}
        self._executor = ThreadPoolExecutor(max_workers=10)

    def register(self, data: PrinterCreate) -> Printer:
        printer_id = str(uuid.uuid4())
        printer = Printer(
            id=printer_id,
            name=data.name,
            host=data.host,
            port=data.port,
        )
        self._printers[printer_id] = printer
        return printer

    def get(self, printer_id: str) -> Optional[Printer]:
        return self._printers.get(printer_id)

    def list_all(self) -> list[Printer]:
        return list(self._printers.values())

    def delete(self, printer_id: str) -> bool:
        if printer_id in self._printers:
            del self._printers[printer_id]
            return True
        return False

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
