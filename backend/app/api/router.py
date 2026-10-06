from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.system import health_router, system_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(system_router, prefix="/v1/system", tags=["system"])
