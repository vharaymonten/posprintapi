import socket
import time
import uuid
import base64
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import jinja2
from jinja2 import TemplateNotFound
from PIL import Image, ImageDraw, ImageFont

from app.core.config import settings
from app.core.print_log import log_print_failure
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

# Maps each byte to its bitwise complement; used to flip PIL's "bit set = white"
# packing into ESC/POS's "bit set = black dot".
_INVERT_BYTE = bytes(255 - i for i in range(256))

# Printer delivery retry policy (tunable via PRINTER_* env vars)
PRINT_MAX_ATTEMPTS = settings.print_max_attempts
PRINT_RETRY_DELAY_SECONDS = settings.print_retry_delay_seconds


class PrintInputError(Exception):
    """Request could not be rendered due to bad input/format (maps to HTTP 400)."""


class PrinterFailureError(Exception):
    """Rendered job could not be delivered to the printer (maps to HTTP 500)."""


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
        self._env.globals["IMAGE_ROW"] = self._image_row_token

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

    def _image_token(
        self,
        path: str,
        height_cm: float = 2.0,
        align: str = "center",
        text: Optional[str] = None,
    ) -> str:
        data = {"path": path, "height_cm": height_cm, "align": align}
        if text is not None:
            data["text"] = str(text)
        payload = base64.b64encode(
            json.dumps(data, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")
        return f"[[[IMG:{payload}]]]"

    def _image_row_token(
        self,
        items,
        height_cm: float = 0.3,
        align: str = "center",
        gap_cm: float = 0.4,
    ) -> str:
        """Compose several logo+text pairs onto a single horizontal band.

        *items* is an iterable of dicts/mappings with ``path`` and optional
        ``text`` keys. The whole row is rendered as one image, so the items
        print side by side on the same line.
        """
        norm = []
        for item in items:
            entry = {"path": item.get("path", "")}
            if item.get("text") is not None:
                entry["text"] = str(item.get("text"))
            norm.append(entry)
        data = {
            "row": norm,
            "height_cm": height_cm,
            "align": align,
            "gap_cm": gap_cm,
        }
        payload = base64.b64encode(
            json.dumps(data, separators=(",", ":")).encode("utf-8")
        ).decode("ascii")
        return f"[[[IMG:{payload}]]]"

    def _compose_logo_text(
        self,
        logo: Image.Image,
        text: str,
        font_px: Optional[int] = None,
        stroke_width: Optional[int] = None,
    ) -> Image.Image:
        """Paste *text* to the right of *logo*, vertically centered, on one band.

        *font_px* overrides the text size (defaults to ~1.2x the logo height).
        *stroke_width* defaults to a faux-bold weight that survives the band
        being scaled down to the print head; callers that already render at
        print size pass 0, since the extra weight fills in small letters.
        """
        h = logo.height
        font_size = font_px if font_px else max(20, int(round(h * 1.2)))
        font = ImageFont.load_default(size=font_size)
        stroke = (
            stroke_width
            if stroke_width is not None
            else max(1, int(round(font_size * 0.08)))  # simulate bold weight
        )
        gap = max(4, int(round(h * 0.25)))
        measure = ImageDraw.Draw(Image.new("L", (1, 1)))
        bbox = measure.textbbox((0, 0), text, font=font, stroke_width=stroke)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        band_h = max(h, text_h)
        canvas = Image.new("L", (logo.width + gap + text_w, band_h), 255)
        ly = (band_h - h) // 2
        canvas.paste(logo, (0, ly))
        draw = ImageDraw.Draw(canvas)
        tx = logo.width + gap - bbox[0]
        ty = (band_h - text_h) // 2 - bbox[1]
        draw.text((tx, ty), text, font=font, fill=0, stroke_width=stroke, stroke_fill=0)
        return canvas

    def _normalize_align(self, align: str) -> str:
        align_normalized = (align or "center").strip().lower()
        if align_normalized not in ("center", "left"):
            raise ValueError(f"Unsupported image align: {align}")
        return align_normalized

    def _load_logo_gray(self, path: str, height_px: int) -> Image.Image:
        """Open *path*, flatten transparency, and resize to *height_px* tall."""
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

            orig_w, orig_h = img.size
            if orig_h <= 0 or orig_w <= 0:
                raise ValueError(f"Invalid image size: {path}")

            logo_w = max(1, int(round(orig_w * (height_px / orig_h))))
            return img.resize((logo_w, height_px), Image.Resampling.LANCZOS)

    def _raster_band_bytes(
        self, img: Image.Image, align: str, *, dither: bool = True
    ) -> bytes:
        """Fit *img* to the receipt text grid and emit an ESC/POS raster.

        A centered image is padded to the full grid width and printed from the
        left margin, so it lines up with ``|center(w)`` text whatever the paper
        width. *dither* suits photographic logos; line art (icons, text) is
        thresholded instead, because dithering its anti-aliased edges prints as
        speckle.
        """
        grid_w = settings.receipt_width_dots
        if img.width > grid_w:
            scaled_h = max(1, int(round(img.height * grid_w / img.width)))
            img = img.resize((grid_w, scaled_h), Image.Resampling.LANCZOS)
        if align == "center" and img.width < grid_w:
            canvas = Image.new("L", (grid_w, img.height), 255)
            canvas.paste(img, ((grid_w - img.width) // 2, 0))
            img = canvas
        new_w, new_h = img.size

        if dither:
            bw = img.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
        else:
            # A light threshold keeps anti-aliased edges as dots, so strokes stay solid.
            bw = img.point(lambda v: 255 if v >= 160 else 0, "1")

        width_bytes = (new_w + 7) // 8
        padded_w = width_bytes * 8
        if padded_w != new_w:
            padded = Image.new("1", (padded_w, new_h), 1)
            padded.paste(bw, (0, 0))
            bw = padded

        # PIL packs mode "1" as one bit per pixel, MSB-first, rows padded to a
        # byte boundary -- exactly the GS v 0 raster layout. It sets a bit for
        # *white*, while ESC/POS sets a bit for a *black dot*, so invert. The
        # padding added above is white, so its bits invert to "no dot".
        raster = bw.tobytes().translate(_INVERT_BYTE)

        xL = width_bytes & 0xFF
        xH = (width_bytes >> 8) & 0xFF
        yL = new_h & 0xFF
        yH = (new_h >> 8) & 0xFF
        image_cmd = GS + b"v0" + bytes([0, xL, xH, yL, yH]) + bytes(raster)
        return LEFT + image_cmd + b"\n"

    def _build_image_bytes(
        self, path: str, height_cm: float, align: str, text: Optional[str] = None
    ) -> bytes:
        align = self._normalize_align(align)
        dpi = 203
        height_px = max(1, int(round((float(height_cm) / 2.54) * dpi)))

        img = self._load_logo_gray(path, height_px)
        if text:
            img = self._compose_logo_text(img, text)

        return self._raster_band_bytes(img, align)

    def _build_image_row_bytes(
        self, items, height_cm: float, align: str, gap_cm: float = 0.4
    ) -> bytes:
        """Render several icon+text pairs side by side on one raster band.

        The band is drawn at the printer's own resolution: *height_cm* is the
        printed icon height and the text starts just under it. If the row is
        wider than the receipt grid, the font steps down until it fits, rather
        than shrinking the finished bitmap -- which smears small text into
        unreadable blobs and shrinks the icons to a few dots.
        """
        align = self._normalize_align(align)
        dpi = 203
        icon_px = max(1, int(round((float(height_cm) / 2.54) * dpi)))
        gap_px = max(0, int(round((float(gap_cm) / 2.54) * dpi)))
        grid_w = settings.receipt_width_dots
        min_font_px = 16  # below this, thermal-printed text stops being legible

        icons = [
            (self._load_logo_gray(str(item.get("path", "")), icon_px), item.get("text"))
            for item in items
        ]
        if not icons:
            raise ValueError("IMAGE_ROW requires at least one item")

        # ~0.9x the icon keeps the text in scale with the printer's 24-dot font.
        font_px = max(min_font_px, int(round(icon_px * 0.9)))
        while True:
            bands = [
                self._compose_logo_text(icon, str(text), font_px=font_px, stroke_width=0)
                if text
                else icon
                for icon, text in icons
            ]
            total_w = sum(b.width for b in bands) + gap_px * (len(bands) - 1)
            if total_w <= grid_w or font_px <= min_font_px:
                break
            font_px -= 1

        max_h = max(b.height for b in bands)
        canvas = Image.new("L", (total_w, max_h), 255)
        x = 0
        for band in bands:
            y = (max_h - band.height) // 2
            canvas.paste(band, (x, y))
            x += band.width + gap_px

        return self._raster_band_bytes(canvas, align, dither=False)

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

            if "row" in payload:
                out.extend(
                    self._build_image_row_bytes(
                        items=payload["row"],
                        height_cm=float(payload.get("height_cm", 0.3)),
                        align=str(payload.get("align", "center")),
                        gap_cm=float(payload.get("gap_cm", 0.4)),
                    )
                )
            else:
                out.extend(
                    self._build_image_bytes(
                        path=str(payload.get("path", "")),
                        height_cm=float(payload.get("height_cm", 2.0)),
                        align=str(payload.get("align", "center")),
                        text=payload.get("text"),
                    )
                )
            pos = match.end()

        out.extend(rendered[pos:].encode("utf-8", errors="ignore"))
        return bytes(out)

    def send_to_printer(
        self,
        printer: Printer,
        content: bytes,
        *,
        job_id: Optional[str] = None,
        template_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Send rendered text content to the thermal printer as ESC/POS.

        The content is treated as plain text (already formatted by Jinja2),
        wrapped with printer INIT and CUT commands.
        """
        # Initialize printer and set to left alignment by default
        buffer = INIT + LEFT + content + b"\n\n\n" + CUT

        for attempt in range(1, PRINT_MAX_ATTEMPTS + 1):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    # Separate budgets: a LAN printer connects in milliseconds,
                    # but the write can legitimately block while paper feeds.
                    sock.settimeout(settings.print_connect_timeout_seconds)
                    sock.connect((printer.host, printer.port))
                    sock.settimeout(settings.print_send_timeout_seconds)
                    sock.sendall(buffer)
                    print(f"[SUCCESS] Print sent to {printer.name} ({printer.host}:{printer.port})")
                    return True
            except Exception as e:
                print(
                    f"[ERROR] Failed to print to {printer.name} "
                    f"({printer.host}:{printer.port}) on attempt "
                    f"{attempt}/{PRINT_MAX_ATTEMPTS}: {e}"
                )
                log_print_failure(
                    "printer_send_failed",
                    "printer_failure",
                    job_id=job_id,
                    template_name=template_name,
                    printer=printer,
                    metadata=metadata,
                    exc=e,
                    attempt=attempt,
                    max_attempts=PRINT_MAX_ATTEMPTS,
                    final=(attempt == PRINT_MAX_ATTEMPTS),
                )
                if attempt < PRINT_MAX_ATTEMPTS:
                    time.sleep(PRINT_RETRY_DELAY_SECONDS)

        return False

    def prepare_print(
        self,
        template_name: str,
        metadata: dict,
        printer_id: Optional[str] = None,
        printer_code: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> tuple[str, Optional[Printer], Optional[bytes], Optional[str]]:
        """Render a job and resolve its printer without touching the network.

        This is everything that can fail on *input*, split out from delivery so
        the API can validate and reject a bad request immediately instead of
        burning a queue slot on it. Returns
        ``(job_id, printer, rendered_bytes, preview)``; ``printer`` is None when
        no printer was requested, in which case ``preview`` holds the render.

        Raises:
            PrintInputError: bad template, unknown printer, or malformed content
                -> HTTP 400.
        """
        job_id = job_id or str(uuid.uuid4())
        try:
            rendered = self.render_template(template_name, metadata)
        except ValueError as e:
            log_print_failure(
                "render_failed",
                "input_error",
                job_id=job_id,
                template_name=template_name,
                metadata=metadata,
                exc=e,
            )
            raise PrintInputError(str(e))

        # Resolve printer by code or ID
        printer = None
        if printer_code:
            printer = printer_service.get_by_code(printer_code, check_availability=False)
            if not printer:
                log_print_failure(
                    "printer_not_found",
                    "input_error",
                    job_id=job_id,
                    template_name=template_name,
                    metadata=metadata,
                    printer_code=printer_code,
                    error=f"Printer not found with code: {printer_code}",
                )
                raise PrintInputError(f"Printer not found with code: {printer_code}")
        elif printer_id:
            printer = printer_service.get(printer_id, check_availability=False)
            if not printer:
                log_print_failure(
                    "printer_not_found",
                    "input_error",
                    job_id=job_id,
                    template_name=template_name,
                    metadata=metadata,
                    printer_id=printer_id,
                    error=f"Printer not found: {printer_id}",
                )
                raise PrintInputError(f"Printer not found: {printer_id}")

        if not printer:
            return job_id, None, None, rendered

        try:
            rendered_bytes = self._rendered_to_bytes(rendered)
        except ValueError as e:
            log_print_failure(
                "image_build_failed",
                "input_error",
                job_id=job_id,
                template_name=template_name,
                printer=printer,
                metadata=metadata,
                exc=e,
            )
            raise PrintInputError(str(e))

        return job_id, printer, rendered_bytes, None

    def initiate_print(
        self,
        template_name: str,
        metadata: dict,
        printer_id: Optional[str] = None,
        printer_code: Optional[str] = None,
    ) -> tuple[bool, str, Optional[str], Optional[str], Optional[str]]:
        """Render and synchronously deliver a job, bypassing the dispatcher.

        Retained for scripts and tests that drive the service directly. The API
        path goes through :class:`~app.core.print_queue.PrintDispatcher` instead,
        so that concurrent jobs for one printer are serialized.

        Raises:
            PrintInputError: the request cannot be rendered -> HTTP 400.
            PrinterFailureError: the job could not be delivered -> HTTP 500.
        """
        job_id, printer, rendered_bytes, preview = self.prepare_print(
            template_name, metadata, printer_id=printer_id, printer_code=printer_code
        )
        if printer is None:
            return True, "Rendered successfully; no printer specified.", job_id, preview, None

        if self.send_to_printer(
            printer,
            rendered_bytes,
            job_id=job_id,
            template_name=template_name,
            metadata=metadata,
        ):
            return True, "Print job sent to printer.", job_id, None, printer.id
        raise PrinterFailureError("Failed to send data to printer.")


print_service = PrintService()
