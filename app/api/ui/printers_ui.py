from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.templates_dir))


@router.get("/ui/printers", response_class=HTMLResponse)
def printers_ui(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("printers.html", {"request": request})

