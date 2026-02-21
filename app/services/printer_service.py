import socket
import uuid
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.models.printer import Printer
from app.schemas.printer import PrinterCreate, PrinterDiscoveryResult


class PrinterService:
    def __init__(self) -> None:
        self._printers: dict[str, Printer] = {}
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._load_printers_from_config()

    def _load_printers_from_config(self) -> None:
        """Load printers from YAML configuration file on startup."""
        config_path = settings.printers_config_path
        if not config_path.exists():
            print(f"Warning: Printers config file not found at {config_path}")
            return
        
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            
            if not config or "printers" not in config:
                print("Warning: No printers found in config file")
                return
            
            for printer_data in config["printers"]:
                printer_id = str(uuid.uuid4())
                printer = Printer(
                    id=printer_id,
                    name=printer_data["name"],
                    printer_code=printer_data.get("printer_code"),
                    host=printer_data["host"],
                    port=printer_data.get("port", settings.default_printer_port),
                )
                self._printers[printer_id] = printer
                code_info = f" [{printer.printer_code}]" if printer.printer_code else ""
                print(f"Loaded printer: {printer.name}{code_info} ({printer.host}:{printer.port})")
        
        except Exception as e:
            print(f"Error loading printers from config: {e}")

    def register(self, data: PrinterCreate) -> Printer:
        printer_id = str(uuid.uuid4())
        printer = Printer(
            id=printer_id,
            name=data.name,
            printer_code=data.printer_code,
            host=data.host,
            port=data.port,
        )
        self._printers[printer_id] = printer
        return printer

    def get(self, printer_id: str) -> Optional[Printer]:
        return self._printers.get(printer_id)

    def get_by_code(self, printer_code: str) -> Optional[Printer]:
        """Get a printer by its printer_code."""
        for printer in self._printers.values():
            if printer.printer_code == printer_code:
                return printer
        return None

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
