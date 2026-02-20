from fastapi import APIRouter, HTTPException

from app.schemas.print_job import InitiatePrintRequest, InitiatePrintResponse
from app.services.print_service import print_service

router = APIRouter()


@router.post("/initiate-print", response_model=InitiatePrintResponse)
def initiate_print(body: InitiatePrintRequest) -> InitiatePrintResponse:
    """
    Render a template with the given metadata and optionally send to a printer.
    Template name is the Jinja2 template file name without .html (e.g. 'receipt' for receipt.html).
    If printer_id is omitted, the rendered HTML is returned in the response for preview/debugging.
    """
    success, message, job_id, html_preview, printer_id = print_service.initiate_print(
        template_name=body.template_name,
        metadata=body.metadata,
        printer_id=body.printer_id,
    )
    if not success and not html_preview:
        raise HTTPException(status_code=400, detail=message)
    return InitiatePrintResponse(
        success=success,
        message=message,
        job_id=job_id,
        html_preview=html_preview,
        printer_id=printer_id,
    )
