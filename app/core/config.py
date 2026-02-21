from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    app_name: str = "Printer API"
    templates_dir: Path = Path(__file__).resolve().parent.parent / "templates"
    # Path to printers YAML configuration file
    printers_config_path: Path = Path(__file__).resolve().parent.parent.parent / "printers.yaml"
    # Default port for raw printing (many thermal printers)
    default_printer_port: int = 9100
    # Discovery: timeout in seconds when scanning for printers
    discovery_timeout_seconds: float = 1.0
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]  # Allow all origins by default, configure as needed
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    class Config:
        env_prefix = "PRINTER_"
        # Allow PRINTER_CORS_ORIGINS="http://localhost:3000,http://localhost:8080"
        env_file = ".env"


settings = Settings()
