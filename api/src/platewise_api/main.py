from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from platewise_api.api.health import router as health_router
from platewise_api.api.v1.router import api_router
from platewise_api.core.config import settings
from platewise_api.core.errors import register_exception_handlers
from platewise_api.schemas import ApiErrorResponse

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(
    api_router,
    prefix="/api/v1",
    # Documents the standard envelope for every versioned route, which also
    # publishes the error schema into OpenAPI for client type generation.
    responses={422: {"description": "Validation error", "model": ApiErrorResponse}},
)
