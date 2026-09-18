from fastapi import APIRouter

from app.api.v1.endpoints import health, ingestion

api_v1_router = APIRouter()

# Include sub-routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(ingestion.router)
