from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Printer API"
    templates_dir: Path = Path(__file__).resolve().parent.parent / "templates"
    # Path to printers YAML configuration file
    printers_config_path: Path = Path(__file__).resolve().parent.parent.parent / "printers.yaml"
    # Default port for raw printing (many thermal printers)
    default_printer_port: int = 9100
    # Discovery: timeout in seconds when scanning for printers
    discovery_timeout_seconds: float = 1.0

    class Config:
        env_prefix = "PRINTER_"


settings = Settings()
