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
    
    # CORS Configuration - Configure in code, not via environment variables
    cors_origins: List[str] = ["*"]  # Allow all origins by default
    cors_credentials: bool = True
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]

    class Config:
        env_prefix = "PRINTER_"
        # Exclude CORS settings from environment variable parsing
        fields = {
            'cors_origins': {'exclude': True},
            'cors_credentials': {'exclude': True},
            'cors_methods': {'exclude': True},
            'cors_headers': {'exclude': True},
        }


settings = Settings()
