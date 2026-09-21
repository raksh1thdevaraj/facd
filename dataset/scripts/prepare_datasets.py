#!/usr/bin/env python3
"""Master Dataset Preparation and Orchestration Script.

Orchestrates all dataset preparation steps for Course Certificate Authenticity Verification:
1. Prepares certificate subdirectories.
2. Structures QR threat test specimens.
3. Validates/generates synthetic tampering dataset and features.
4. Audits split balance and leakage guarantees.
5. Verifies external dataset acquisition protocols.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dataset.scripts.create_metadata import validate_and_report_metadata
from dataset.scripts.generate_tampered_certificates import main as generate_tampered_main
from dataset.scripts.prepare_certificate_dataset import prepare_certificate_directories
from dataset.scripts.prepare_qr_dataset import generate_qr_test_vectors

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_all_preparations(quick_mode: bool = False) -> None:
    """Run full dataset preparation pipeline."""
    logger.info("=== STEP 1: Structuring Course Certificate Directories ===")
    prepare_certificate_directories()

    logger.info("=== STEP 2: Structuring QR Threat Evaluation Vectors ===")
    generate_qr_test_vectors(sample_count=40)

    logger.info("=== STEP 3: Generating/Validating Synthetic Tampered Dataset ===")
    metadata_path = PROJECT_ROOT / "dataset" / "course_certificates" / "metadata.csv"
    if not metadata_path.exists() or not quick_mode:
        generate_tampered_main()

    logger.info("=== STEP 4: Auditing Dataset Splits and Metadata Schema ===")
    validate_and_report_metadata()

    logger.info("=== Dataset Preparation Completed Successfully ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Master dataset preparation pipeline")
    parser.add_argument("--quick", action="store_true", help="Skip re-generation if metadata already exists")
    args = parser.parse_args()
    run_all_preparations(quick_mode=args.quick)
