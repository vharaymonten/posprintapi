from pydantic import BaseModel
from typing import Optional


class Printer(BaseModel):
    id: str
    name: str
    host: str
    port: int = 9100
    is_available: Optional[bool] = None
