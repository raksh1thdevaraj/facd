from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    audit,
    auth,
    certificates,
    course_certificates,
    health,
    ingestion,
    institutions,
    records,
    reports,
    templates,
    verification_hub,
    verifications_history,
)

api_v1_router = APIRouter()

# Include sub-routers
api_v1_router.include_router(auth.router)
api_v1_router.include_router(health.router)
api_v1_router.include_router(verification_hub.router)
api_v1_router.include_router(verifications_history.router, prefix="/verifications/history", tags=["Verification History"])
api_v1_router.include_router(ingestion.router)
api_v1_router.include_router(certificates.router)
api_v1_router.include_router(course_certificates.router)
api_v1_router.include_router(institutions.router)
api_v1_router.include_router(templates.router)
api_v1_router.include_router(records.router)
api_v1_router.include_router(reports.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(admin.router)
