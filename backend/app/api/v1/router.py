from fastapi import APIRouter

from app.api.v1.endpoints import (
    audit,
    certificates,
    health,
    ingestion,
    institutions,
    records,
    reports,
    templates,
)

api_v1_router = APIRouter()

# Include sub-routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(ingestion.router)
api_v1_router.include_router(certificates.router)
api_v1_router.include_router(institutions.router)
api_v1_router.include_router(templates.router)
api_v1_router.include_router(records.router)
api_v1_router.include_router(reports.router)
api_v1_router.include_router(audit.router)
