from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.templates_dir.mkdir(parents=True, exist_ok=True)
    yield


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

app.include_router(api_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
