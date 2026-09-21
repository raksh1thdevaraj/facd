"""Orphan file garbage collection and temporary scratch space purger."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.certificate import CertificateModel

logger = logging.getLogger(__name__)


class CleanupService:
    """Purges orphaned temporary uploads, rasterized images, and scratch artifacts
    older than the retention threshold.
    """

    @staticmethod
    def cleanup_orphaned_files(
        max_age_hours: int = 48,
        custom_dirs: Optional[List[Path]] = None,
        db: Optional[Session] = None,
    ) -> int:
        """Scan and purge temporary files older than max_age_hours.

        Returns total number of deleted files.
        """
        now = time.time()
        max_age_seconds = max_age_hours * 3600
        deleted_count = 0

        target_dirs = custom_dirs or [
            settings.UPLOAD_DIR / "rasterized",
            settings.UPLOAD_DIR / "preprocessed",
            settings.REPORT_DIR,
        ]

        active_paths = set()
        if db is not None:
            try:
                active_certs = db.query(CertificateModel).all()
                for c in active_certs:
                    if c.file_path:
                        active_paths.add(Path(c.file_path).resolve())
                    if c.preprocessed_image_path:
                        active_paths.add(Path(c.preprocessed_image_path).resolve())
            except Exception as e:
                logger.warning("Could not query active certificates for cleanup: %s", e)

        for directory in target_dirs:
            p = Path(directory)
            if not p.exists():
                continue
            for item in p.glob("*"):
                if item.is_file():
                    # ponytail: skip active files tracked in database
                    if item.resolve() in active_paths:
                        continue
                    file_age = now - item.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            item.unlink()
                            deleted_count += 1
                        except Exception as e:
                            logger.error("Failed to delete orphaned file %s: %s", item, e)

        logger.info(
            "Cleanup completed: %d orphaned files removed (older than %dh)",
            deleted_count,
            max_age_hours,
        )
        return deleted_count
