import asyncio
import functools

import anyio.to_thread
from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.print_queue import PrintJob, QueueFullError, get_dispatcher
from app.schemas.print_job import InitiatePrintRequest, InitiatePrintResponse
from app.services.print_service import (
    print_service,
    PrintInputError,
    PrinterFailureError,
)

router = APIRouter()


@router.post("/initiate-print", response_model=InitiatePrintResponse)
async def initiate_print(body: InitiatePrintRequest) -> InitiatePrintResponse:
    """
    Render a template with the given metadata and optionally send to a printer.
    Template name is the Jinja2 template file name (e.g. 'receipt.txt'); a name
    without an extension is resolved as '.html'.
    If no printer is specified, the rendered output is returned for preview.

    A printer accepts one connection at a time, so jobs are queued per printer
    and delivered by a single serialized worker. The request waits up to
    ``print_wait_timeout_seconds`` for its receipt, so a 200 still means the
    bytes reached the printer.

    Returns 400 when the input cannot be rendered (bad template, unknown printer,
    or malformed content), 500 when the printer rejected the job, and 503 with
    Retry-After when the printer's backlog is full or the job did not reach the
    printer within the wait budget.
    """
    # Render off the event loop: Jinja2 plus any logo rasterization is CPU work.
    # Doing it before enqueueing means malformed requests fail fast with a 400
    # instead of occupying a queue slot behind real jobs.
    try:
        job_id, printer, rendered_bytes, preview = await anyio.to_thread.run_sync(
            functools.partial(
                print_service.prepare_print,
                body.template_name,
                body.metadata,
                printer_id=body.printer_id,
                printer_code=body.printer_code,
            )
        )
    except PrintInputError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if printer is None:
        return InitiatePrintResponse(
            success=True,
            message="Rendered successfully; no printer specified.",
            job_id=job_id,
            html_preview=preview,
            printer_id=None,
        )

    job = PrintJob(
        job_id=job_id,
        printer_key=printer.id,
        send=functools.partial(
            print_service.send_to_printer,
            printer,
            rendered_bytes,
            job_id=job_id,
            template_name=body.template_name,
            metadata=body.metadata,
        ),
    )

    dispatcher = get_dispatcher()
    try:
        await dispatcher.submit(job)
    except QueueFullError as e:
        # Must go on the exception: headers set on the injected Response are
        # discarded once an HTTPException unwinds the handler.
        raise HTTPException(status_code=503, detail=str(e), headers={"Retry-After": "1"})

    try:
        delivered = await asyncio.wait_for(
            asyncio.shield(job.future), timeout=settings.print_wait_timeout_seconds
        )
    except asyncio.TimeoutError:
        if job.try_abandon():
            # Still queued, so it is guaranteed not to reach the printer and the
            # caller can safely retry without risking a duplicate receipt.
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Timed out after {settings.print_wait_timeout_seconds}s waiting for "
                    f"printer {printer.name}; job {job_id} was dropped and did not print."
                ),
                headers={"Retry-After": "1"},
            )
        # Already on the wire. Waiting out the socket timeouts keeps the response
        # truthful rather than reporting a failure for a receipt that printed.
        try:
            delivered = await job.future
        except Exception as e:  # noqa: BLE001 - reported as a printer failure
            raise HTTPException(status_code=500, detail=str(e))

    if not delivered:
        raise HTTPException(status_code=500, detail="Failed to send data to printer.")

    return InitiatePrintResponse(
        success=True,
        message="Print job sent to printer.",
        job_id=job_id,
        html_preview=None,
        printer_id=printer.id,
    )


@router.get("/print-queue")
def print_queue_stats() -> dict:
    """Per-printer backlog depth, for monitoring saturation before it bites."""
    return get_dispatcher().stats()
