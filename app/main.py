from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.api.ui import ui_router
from app.core import error_log, print_queue
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    error_log.start()
    settings.templates_dir.mkdir(parents=True, exist_ok=True)

    # The dispatcher owns asyncio queues and tasks, so it must be built inside
    # the running loop rather than at import time.
    print_queue.dispatcher = print_queue.build_dispatcher()
    try:
        yield
    finally:
        await print_queue.dispatcher.aclose()
        print_queue.dispatcher = None
        # Last, so anything logged while draining the print queue is flushed.
        error_log.stop()


app = FastAPI(
    title=settings.app_name,
    description="API for thermal printers on local networks (restaurant use). Uses HTML templates with Jinja2.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# JSON error log with traceback and request payload for every 4xx/5xx
error_log.install(app)

app.include_router(api_router)
app.include_router(ui_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
