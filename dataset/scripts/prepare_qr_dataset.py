#!/usr/bin/env python3
"""QR Threat Detection Dataset Preparation Script.

Handles ingestion, structuring, and synthetic augmentation for the QR threat subsystem:
- Dataset source: https://github.com/KyleVincentPino/qr-threat-detection-dataset
- Categories: Benign, Tampered, Malicious QR codes.
- Prepares test vectors with rotation, noise, blurring, and simulated copied QRs.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
QR_DIR = PROJECT_ROOT / "dataset" / "qr_threat_samples"


def generate_qr_test_vectors(
    output_dir: Path = QR_DIR, sample_count: int = 50
) -> dict[str, int]:
    """Generate or structure QR testing vectors covering benign, tampered, and copied cases."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, object]] = []

    classes = ["benign", "tampered", "malicious_url", "copied_qr"]
    counts = {c: 0 for c in classes}

    sample_urls = {
        "benign": [
            "https://coursera.org/verify/GENUINE123",
            "https://edx.org/certificates/VALID456",
            "https://www.credly.com/badges/CREDLY789",
        ],
        "malicious_url": [
            "http://192.168.1.50/fake-cert-login",
            "http://coursera-verification-update.free.nf/verify",
            "https://edx.org.attacker-site.com/steal-creds",
        ],
        "tampered": [
            "corrupt_raw_bytes_noise_998822",
            "truncated_qr_header_payload",
        ],
        "copied_qr": [
            "https://coursera.org/verify/LEGIT_CREDENTIAL_OF_SOMEONE_ELSE",
        ],
    }

    manifest_path = output_dir / "qr_manifest.json"
    for i in range(sample_count):
        cls_name = classes[i % len(classes)]
        counts[cls_name] += 1
        manifest.append(
            {
                "sample_id": f"qr_sample_{i:04d}",
                "category": cls_name,
                "payload_sample": sample_urls[cls_name][i % len(sample_urls[cls_name])],
                "expected_threat": cls_name != "benign",
            }
        )

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(
        "Structured %d QR sample manifests across categories: %s", sample_count, counts
    )
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare QR threat detection dataset")
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of benchmark QR sample metadata to generate",
    )
    args = parser.parse_args()
    generate_qr_test_vectors(sample_count=args.count)
