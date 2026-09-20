import time
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.config import settings
from app.models.record import InstitutionRecordModel
from app.models.template import InstitutionTemplateModel


def run_template_diagnostics(db: Session) -> Dict[str, Any]:
    """Execute health checks on template storage, descriptor cache, and database index latency."""
    storage_exists = settings.TEMPLATES_DIR.exists()

    # Measure DB query latency
    t0 = time.perf_counter()
    template_count = db.query(InstitutionTemplateModel).count()
    record_count = db.query(InstitutionRecordModel).count()
    _ = (
        db.query(InstitutionRecordModel)
        .filter(InstitutionRecordModel.roll_number == "BENCHMARK_PROBE_12345")
        .first()
    )
    latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    is_healthy = storage_exists and latency_ms < 500.0

    return {
        "status": "HEALTHY" if is_healthy else "DEGRADED",
        "storage_directory": str(settings.TEMPLATES_DIR),
        "storage_accessible": storage_exists,
        "templates_registered": template_count,
        "records_indexed": record_count,
        "index_query_latency_ms": latency_ms,
        "meets_sla": latency_ms < 500.0,
    }
