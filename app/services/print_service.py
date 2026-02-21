import socket
import uuid
from pathlib import Path
from typing import Optional

import jinja2
from jinja2 import TemplateNotFound

from app.core.config import settings
from app.models.printer import Printer
from app.services.printer_service import printer_service


# --- ESC/POS RAW COMMANDS (same as standalone script) ---
ESC = b"\x1b"
GS = b"\x1d"
INIT = ESC + b"@"
CUT = GS + b"V\x00"


class PrintService:
    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        receipt_templates_dir = base_dir / "receipt_templates"

        # Load from both the original app templates and the new
        # plain-text receipt templates directory.
        self._env = jinja2.Environment(
            loader=jinja2.ChoiceLoader(
                [
                    jinja2.FileSystemLoader(str(settings.templates_dir)),
                    jinja2.FileSystemLoader(str(receipt_templates_dir)),
                ]
            ),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_template(self, template_name: str, metadata: dict) -> str:
        """Render a Jinja2 template by name with the given metadata.

        If *template_name* includes a file extension (e.g. ``receipt.txt`` or
        ``receipt.html``) it is used as-is. If no extension is provided,
        ``.html`` is assumed for backwards compatibility with existing code.
        """
        suffix = Path(template_name).suffix
        if suffix:
            name = template_name
        else:
            name = f"{template_name}.html"
        try:
            template = self._env.get_template(name)
        except TemplateNotFound:
            raise ValueError(f"Template not found: {template_name}")
        return template.render(**metadata)

    def send_to_printer(self, printer: Printer, content: str) -> bool:
        """Send rendered text content to the thermal printer as ESC/POS.

        The content is treated as plain text (already formatted by Jinja2),
        wrapped with printer INIT and CUT commands.
        """
        buffer = INIT + content.encode("utf-8") + b"\n\n\n" + CUT

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((printer.host, printer.port))
                sock.sendall(buffer)
                return True
        except Exception:
            return False

    def initiate_print(
        self,
        template_name: str,
        metadata: dict,
        printer_id: Optional[str] = None,
        printer_code: Optional[str] = None,
    ) -> tuple[bool, str, Optional[str], Optional[str], Optional[str]]:
        """
        Render template and optionally send to printer.
        Accepts either printer_id or printer_code. If both provided, printer_code takes precedence.
        Returns: (success, message, job_id, html_preview, printer_id)
        """
        job_id = str(uuid.uuid4())
        try:
            rendered = self.render_template(template_name, metadata)
        except ValueError as e:
            return False, str(e), None, None, None

        # Resolve printer by code or ID
        printer = None
        if printer_code:
            printer = printer_service.get_by_code(printer_code)
            if not printer:
                return False, f"Printer not found with code: {printer_code}", job_id, rendered, None
        elif printer_id:
            printer = printer_service.get(printer_id)
            if not printer:
                return False, f"Printer not found: {printer_id}", job_id, rendered, None
        
        if not printer:
            return True, "Rendered successfully; no printer specified.", job_id, rendered, None

        if self.send_to_printer(printer, rendered):
            return True, "Print job sent to printer.", job_id, None, printer.id
        return False, "Failed to send data to printer.", job_id, rendered, printer.id


print_service = PrintService()
