from fastapi import APIRouter

from platewise_api.core.config import settings
from platewise_api.schemas import StatusResponse

router = APIRouter(tags=["status"])


@router.get("/status", response_model=StatusResponse)
def service_status() -> StatusResponse:
    return StatusResponse(service=settings.app_name, environment=settings.app_env)
