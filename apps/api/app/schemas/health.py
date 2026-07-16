from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    api: Literal["ok"] = "ok"
    database: Literal["ok", "unavailable"]


class StatusResponse(BaseModel):
    service: str
    status: Literal["ok"] = "ok"
    environment: str
