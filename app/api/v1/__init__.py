from fastapi import APIRouter
from .print import router as print_router
from .printers import router as printers_router

api_router = APIRouter(prefix="/api/v1", tags=["v1"])
api_router.include_router(print_router, tags=["print"])
api_router.include_router(printers_router, prefix="/printers", tags=["printers"])
