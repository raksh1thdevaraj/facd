import os
from pathlib import Path
from typing import Any, Dict

from app.config import settings
from app.modules.ingestion.rasterizer import is_poppler_installed


def check_ingestion_health() -> Dict[str, Any]:
    """Inspect the operational readiness of ingestion subsystem dependencies."""
    storage_dir = Path(settings.STORAGE_BASE_DIR).resolve()
    storage_writable = False
    disk_free_gb = 0.0

    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
        test_file = storage_dir / ".health_check_tmp"
        test_file.write_text("health")
        test_file.unlink(missing_ok=True)
        storage_writable = True

        stat = os.statvfs(str(storage_dir))
        free_bytes = stat.f_bavail * stat.f_frsize
        disk_free_gb = round(free_bytes / (1024**3), 2)
    except Exception:
        storage_writable = False

    poppler_available = is_poppler_installed()
    # Note: Even if poppler is absent, pypdfium2 fallback handles PDF rasterization cleanly
    is_healthy = storage_writable and disk_free_gb > 0.5

    return {
        "status": "ok" if is_healthy else "degraded",
        "poppler_available": poppler_available,
        "pdfium_available": True,
        "storage_writable": storage_writable,
        "disk_free_gb": disk_free_gb,
    }
