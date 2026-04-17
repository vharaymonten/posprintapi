import socket
import uuid
import base64
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import jinja2
from jinja2 import TemplateNotFound
from PIL import Image

from app.core.config import settings
from app.models.printer import Printer
from app.services.printer_service import printer_service


# --- ESC/POS RAW COMMANDS ---
ESC = b"\x1b"
GS = b"\x1d"
INIT = ESC + b"@"
CENTER = ESC + b"a\x01"
LEFT = ESC + b"a\x00"
BOLD_ON = ESC + b"E\x01"
BOLD_OFF = ESC + b"E\x00"
DOUBLE_HEIGHT_ON = ESC + b"!\x10"
DOUBLE_WIDTH_ON = ESC + b"!\x20"
DOUBLE_SIZE_ON = ESC + b"!\x30"  # Double height + width
NORMAL_SIZE = ESC + b"!\x00"
CUT = GS + b"V\x00"


class PrintService:
    def __init__(self) -> None:
        self._base_dir = Path(__file__).resolve().parents[2]
        receipt_templates_dir = self._base_dir / "receipt_templates"

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
        
        # Add custom filters for text formatting
        self._env.filters['rjust'] = lambda s, width, fillchar=' ': str(s).rjust(width, fillchar)
        self._env.filters['ljust'] = lambda s, width, fillchar=' ': str(s).ljust(width, fillchar)
        self._env.filters['truncate'] = lambda s, length, end='...': str(s)[:length] if len(str(s)) <= length else str(s)[:length-len(end)] + end
        self._env.globals["IMAGE"] = self._image_token

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
        
        # Ensure a time field and timestamp exist (UTC+7) if not provided
        tz_utc_plus_7 = timezone(timedelta(hours=7))
        now_utc7 = datetime.now(tz_utc_plus_7)
        if "date" not in metadata:
            metadata = {**metadata, "date": now_utc7.strftime("%Y-%m-%d")}
        if "time" not in metadata:
            metadata = {**metadata, "time": now_utc7.strftime("%H:%M:%S")}
        if "timestamp" not in metadata:
            # Example format: 06-03-2026 04:46 PM
            metadata = {**metadata, "timestamp": now_utc7.strftime("%d-%m-%Y %I:%M %p")}

        # Add ESC/POS commands to template context
        template_context = {
            **metadata,
            'INIT': INIT.decode('latin-1'),
            'CENTER': CENTER.decode('latin-1'),
            'LEFT': LEFT.decode('latin-1'),
            'BOLD_ON': BOLD_ON.decode('latin-1'),
            'BOLD_OFF': BOLD_OFF.decode('latin-1'),
            'DOUBLE_HEIGHT_ON': DOUBLE_HEIGHT_ON.decode('latin-1'),
            'DOUBLE_WIDTH_ON': DOUBLE_WIDTH_ON.decode('latin-1'),
            'DOUBLE_SIZE_ON': DOUBLE_SIZE_ON.decode('latin-1'),
            'NORMAL_SIZE': NORMAL_SIZE.decode('latin-1'),
            'CUT': CUT.decode('latin-1'),
        }
        
        return template.render(**template_context)

    def _image_token(self, path: str, height_cm: float = 2.0, align: str = "center") -> str:
        payload = base64.b64encode(
            json.dumps(
                {"path": path, "height_cm": height_cm, "align": align},
                separators=(",", ":"),
            ).encode("utf-8")
        ).decode("ascii")
        return f"[[[IMG:{payload}]]]"

    def _build_image_bytes(self, path: str, height_cm: float, align: str) -> bytes:
        align_normalized = (align or "center").strip().lower()
        if align_normalized == "center":
            align_bytes = CENTER
        elif align_normalized == "left":
            align_bytes = LEFT
        else:
            raise ValueError(f"Unsupported image align: {align}")

        img_path = (self._base_dir / path).resolve()
        if not img_path.exists():
            raise ValueError(f"Image not found: {path}")

        with Image.open(img_path) as img:
            if img.mode in ("RGBA", "LA") or ("transparency" in img.info):
                rgba = img.convert("RGBA")
                bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                img = Image.alpha_composite(bg, rgba).convert("RGB")
            else:
                img = img.convert("RGB")

            img = img.convert("L")

            dpi = 203
            height_px = max(1, int(round((float(height_cm) / 2.54) * dpi)))

            orig_w, orig_h = img.size
            if orig_h <= 0 or orig_w <= 0:
                raise ValueError(f"Invalid image size: {path}")

            new_w = max(1, int(round(orig_w * (height_px / orig_h))))
            new_h = height_px

            max_width_dots = 384
            if new_w > max_width_dots:
                scale = max_width_dots / new_w
                new_w = max(1, int(round(new_w * scale)))
                new_h = max(1, int(round(new_h * scale)))

            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            bw = img.convert("1", dither=Image.Dither.FLOYDSTEINBERG)

            width_bytes = (new_w + 7) // 8
            padded_w = width_bytes * 8
            if padded_w != new_w:
                padded = Image.new("1", (padded_w, new_h), 1)
                padded.paste(bw, (0, 0))
                bw = padded

            pixels = bw.load()
            raster = bytearray()
            for y in range(new_h):
                for xb in range(width_bytes):
                    b = 0
                    for bit in range(8):
                        x = xb * 8 + bit
                        if pixels[x, y] == 0:
                            b |= 1 << (7 - bit)
                    raster.append(b)

            xL = width_bytes & 0xFF
            xH = (width_bytes >> 8) & 0xFF
            yL = new_h & 0xFF
            yH = (new_h >> 8) & 0xFF
            image_cmd = GS + b"v0" + bytes([0, xL, xH, yL, yH]) + bytes(raster)
            return align_bytes + image_cmd + b"\n" + LEFT

    def _rendered_to_bytes(self, rendered: str) -> bytes:
        pattern = re.compile(r"\[\[\[IMG:([A-Za-z0-9+/=]+)\]\]\]")
        out = bytearray()
        pos = 0
        for match in pattern.finditer(rendered):
            out.extend(rendered[pos:match.start()].encode("utf-8", errors="ignore"))
            payload_b64 = match.group(1)
            try:
                payload_json = base64.b64decode(payload_b64).decode("utf-8")
                payload = json.loads(payload_json)
            except Exception as e:
                raise ValueError(f"Invalid image token payload: {e}")

            out.extend(
                self._build_image_bytes(
                    path=str(payload.get("path", "")),
                    height_cm=float(payload.get("height_cm", 2.0)),
                    align=str(payload.get("align", "center")),
                )
            )
            pos = match.end()

        out.extend(rendered[pos:].encode("utf-8", errors="ignore"))
        return bytes(out)

    def send_to_printer(self, printer: Printer, content: bytes) -> bool:
        """Send rendered text content to the thermal printer as ESC/POS.

        The content is treated as plain text (already formatted by Jinja2),
        wrapped with printer INIT and CUT commands.
        """
        # Initialize printer and set to left alignment by default
        buffer = INIT + LEFT + content + b"\n\n\n" + CUT

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((printer.host, printer.port))
                sock.sendall(buffer)
                print(f"[SUCCESS] Print sent to {printer.name} ({printer.host}:{printer.port})")
                return True
        except Exception as e:
            print(f"[ERROR] Failed to print to {printer.name} ({printer.host}:{printer.port}): {e}")
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

        try:
            rendered_bytes = self._rendered_to_bytes(rendered)
        except ValueError as e:
            return False, str(e), job_id, rendered, printer.id

        if self.send_to_printer(printer, rendered_bytes):
            return True, "Print job sent to printer.", job_id, None, printer.id
        return False, "Failed to send data to printer.", job_id, rendered, printer.id


print_service = PrintService()
