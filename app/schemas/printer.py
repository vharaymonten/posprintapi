from pydantic import BaseModel, Field
from typing import Optional


class PrinterCreate(BaseModel):
    name: str = Field(..., description="Friendly name for the printer")
    host: str = Field(..., description="IP or hostname of the printer")
    port: int = Field(9100, description="Port (typically 9100 for raw printing)")


class PrinterResponse(BaseModel):
    id: str
    name: str
    host: str
    port: int
    is_available: Optional[bool] = None


class PrinterDiscoveryResult(BaseModel):
    host: str
    port: int
    reachable: bool
