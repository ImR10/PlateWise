from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from platewise_api.api.health import router as health_router
from platewise_api.api.v1.router import api_router
from platewise_api.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")
