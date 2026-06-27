from typing import Any
from pydantic import BaseModel


class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Any = None
