from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas.health import HealthCheckResponse, ServiceStatus

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check and service status probe",
)
def get_health(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """Probe the health of the FastAPI service and its dependencies (Database, Storage)."""
    # 1. Probe database connectivity
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # 2. Probe storage accessibility
    storage_status = "accessible"
    try:
        settings.ensure_directories_exist()
    except Exception:
        storage_status = "inaccessible"

    is_healthy = db_status == "connected" and storage_status == "accessible"
    overall_status = "ok" if is_healthy else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        version="0.1.0",
        services=ServiceStatus(
            database=db_status,
            redis="disabled" if not settings.USE_ASYNC_CELERY else "enabled",
            storage=storage_status,
        ),
    )


@router.get(
    "/health/ingestion",
    status_code=status.HTTP_200_OK,
    summary="Ingestion subsystem health probe",
)
def get_ingestion_health() -> dict:
    """Probe the health of document ingestion dependencies (PDF renderers, disk storage)."""
    from app.modules.ingestion.health import check_ingestion_health

    return check_ingestion_health()
