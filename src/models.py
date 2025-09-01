from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class MCPError(BaseModel):
    code: str
    message: str


class MCPResponse(BaseModel):
    success: bool
    data: Any | None = None
    error: MCPError | None = None
