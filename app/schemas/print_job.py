from pydantic import BaseModel, Field
from typing import Any, Optional


class InitiatePrintRequest(BaseModel):
    template_name: str = Field(..., description="Name of the Jinja2 template to render (without .html)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Data to populate the template")
    printer_id: Optional[str] = Field(None, description="Target printer ID; if omitted, returns rendered HTML only")


class InitiatePrintResponse(BaseModel):
    success: bool
    message: str
    job_id: Optional[str] = None
    html_preview: Optional[str] = None
    printer_id: Optional[str] = None
