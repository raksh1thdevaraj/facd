#!/usr/bin/env python3
"""Course Certificate Dataset Preparation & Directory Structuring Script.

Initializes, cleans, and structures directory trees for:
- Genuine course certificates (Coursera, edX, Udemy, Stanford, etc.)
- Controlled tampered variants (name, cert_id, course, date, grade, logo, seal, signature, qr_copied)
- Generates template metadata if none exists.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CERT_DIR = PROJECT_ROOT / "dataset" / "course_certificates"

SUBDIRS = [
    "genuine",
    "tampered/name_changed",
    "tampered/certificate_id_changed",
    "tampered/date_changed",
    "tampered/course_changed",
    "tampered/grade_changed",
    "tampered/logo_changed",
    "tampered/seal_changed",
    "tampered/signature_changed",
    "tampered/qr_replaced",
    "tampered/qr_copied",
    "tampered/multiple_fields",
    "synthetic",
]


def prepare_certificate_directories(base_dir: Path = CERT_DIR) -> None:
    """Ensure all required certificate dataset subdirectories exist."""
    base_dir.mkdir(parents=True, exist_ok=True)
    created = 0
    for sub in SUBDIRS:
        sub_path = base_dir / sub
        if not sub_path.exists():
            sub_path.mkdir(parents=True, exist_ok=True)
            # Add .gitkeep so git tracks empty directory structure without raw images
            (sub_path / ".gitkeep").touch()
            created += 1

    logger.info("Checked/created %d course certificate subdirectories under %s", len(SUBDIRS), base_dir)


if __name__ == "__main__":
    prepare_certificate_directories()
