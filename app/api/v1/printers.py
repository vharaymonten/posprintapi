from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.printer import PrinterCreate, PrinterResponse, PrinterDiscoveryResult
from app.services.printer_service import printer_service

router = APIRouter()


@router.get("", response_model=list[PrinterResponse])
def list_printers() -> list[PrinterResponse]:
    """List all registered printers."""
    printers = printer_service.list_all()
    return [
        PrinterResponse(
            id=p.id,
            name=p.name,
            printer_code=p.printer_code,
            host=p.host,
            port=p.port,
            is_available=p.is_available,
        )
        for p in printers
    ]


@router.post("", response_model=PrinterResponse, status_code=201)
def register_printer(data: PrinterCreate) -> PrinterResponse:
    """Register a new printer by host and port."""
    printer = printer_service.register(data)
    return PrinterResponse(
        id=printer.id,
        name=printer.name,
        printer_code=printer.printer_code,
        host=printer.host,
        port=printer.port,
        is_available=printer.is_available,
    )


@router.get("/discover", response_model=list[PrinterDiscoveryResult])
def discover_printers(
    network: Optional[str] = Query(
        "192.168.1",
        description="Network prefix to scan (e.g. 192.168.1 for 192.168.1.1-254)",
    ),
    port: int = Query(9100, description="Port to check (default 9100 for raw printing"),
) -> list[PrinterDiscoveryResult]:
    """Scan the local network for devices with the printer port open (e.g. 9100)."""
    results = printer_service.discover_on_network(network_prefix=network, port=port)
    return results


@router.get("/{printer_id}", response_model=PrinterResponse)
def get_printer(printer_id: str) -> PrinterResponse:
    """Get a registered printer by ID."""
    printer = printer_service.get(printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return PrinterResponse(
        id=printer.id,
        name=printer.name,
        printer_code=printer.printer_code,
        host=printer.host,
        port=printer.port,
        is_available=printer.is_available,
    )


@router.delete("/{printer_id}", status_code=204)
def delete_printer(printer_id: str) -> None:
    """Remove a printer from the registry."""
    if not printer_service.delete(printer_id):
        raise HTTPException(status_code=404, detail="Printer not found")
