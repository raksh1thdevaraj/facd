import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from pathlib import Path

from app.config import settings
from app.database import get_db
from app.schemas.health import HealthCheckResponse, LightweightHealthResponse, ServiceStatus

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Health check and service status probe",
)
def get_health(db: Session = Depends(get_db)) -> dict:
    """Probe the health of the FastAPI service and its dependencies (Database, Storage, Models)."""
    start_time = time.perf_counter()

    # 1. Probe database connectivity
    db_status = "disconnected"
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
        db_connected = True
    except Exception:
        db_status = "disconnected"
        db_connected = False

    # 2. Probe storage accessibility
    storage_status = "accessible"
    try:
        settings.ensure_directories_exist()
    except Exception:
        storage_status = "inaccessible"

    # 3. Probe model engine status
    model_dir = Path(settings.MODEL_DIR)
    model_online = model_dir.exists()
    model_engine_status = "online" if model_online else "degraded"

    latency_ms = max(1.0, round((time.perf_counter() - start_time) * 1000.0, 1))

    is_healthy = db_connected and storage_status == "accessible"
    overall_status = "healthy" if is_healthy else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db_connected": db_connected,
        "model_engine": model_engine_status,
        "latency_ms": latency_ms,
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
        "services": {
            "database": db_status,
            "redis": "disabled" if not settings.USE_ASYNC_CELERY else "enabled",
            "storage": storage_status,
        },
    }



@router.get(
    "/health/ingestion",
    status_code=status.HTTP_200_OK,
    summary="Ingestion subsystem health probe",
)
def get_ingestion_health() -> dict:
    """Probe the health of document ingestion dependencies (PDF renderers, disk storage)."""
    from app.modules.ingestion.health import check_ingestion_health

    return check_ingestion_health()


@router.get(
    "/health/detailed",
    status_code=status.HTTP_200_OK,
    summary="Detailed diagnostic health probe across all subsystems",
)
def get_detailed_health(db: Session = Depends(get_db)) -> dict:
    """Perform diagnostic health checks across database, storage, and ML models."""
    from pathlib import Path

    # 1. DB check
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # 2. Storage check
    upload_ok = Path(settings.UPLOAD_DIR).exists()
    reports_ok = Path(settings.REPORT_DIR).exists()

    # 3. Models check
    rf_model_ok = (Path(settings.MODEL_DIR) / "baseline_model_v1.joblib").exists()
    meta_model_ok = (Path(settings.MODEL_DIR) / "meta_classifier.joblib").exists()

    all_ok = db_ok and upload_ok and reports_ok

    return {
        "status": "healthy" if all_ok else "degraded",
        "database": {"connected": db_ok, "dialect": settings.DATABASE_URL.split("://")[0]},
        "storage": {
            "upload_dir": str(settings.UPLOAD_DIR),
            "upload_dir_exists": upload_ok,
            "report_dir": str(settings.REPORT_DIR),
            "report_dir_exists": reports_ok,
        },
        "models": {
            "random_forest_baseline": rf_model_ok,
            "stacking_meta_classifier": meta_model_ok,
        },
    }
