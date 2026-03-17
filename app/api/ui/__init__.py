from fastapi import APIRouter

from .printers_ui import router as printers_ui_router

ui_router = APIRouter()
ui_router.include_router(printers_ui_router, tags=["ui"])

