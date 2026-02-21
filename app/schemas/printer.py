from pydantic import BaseModel, Field
from typing import Optional


class PrinterCreate(BaseModel):
    name: str = Field(..., description="Friendly name for the printer")
    printer_code: Optional[str] = Field(None, description="Unique printer code (e.g. KITCHEN, BAR)")
    host: str = Field(..., description="IP or hostname of the printer")
    port: int = Field(9100, description="Port (typically 9100 for raw printing)")


class PrinterResponse(BaseModel):
    id: str
    name: str
    printer_code: Optional[str] = None
    host: str
    port: int
    is_available: Optional[bool] = None


class PrinterDiscoveryResult(BaseModel):
    host: str
    port: int
    reachable: bool
