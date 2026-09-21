#!/usr/bin/env python3
"""Synthetic Course Certificate & Tampering Generator (Phase 9).

Synthesizes controlled manipulations across course certificates for empirical ML training:
- Genuine samples with valid QRs and matching online records
- Name replacements
- Certificate ID replacements
- Date replacements
- Course title replacements
- Grade & score replacements
- Logo & seal modifications
- Signature modifications
- Broken/tampered QRs
- Copied/transplanted QRs (Valid QR pointing to credential A pasted on certificate B)
- Multiple-field manipulations

Enforces group-based train/val/test splitting to prevent template data leakage.
"""

from __future__ import annotations

import csv
import logging
import random
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "dataset" / "course_certificates"
METADATA_FILE = OUTPUT_DIR / "metadata.csv"
FEATURES_FILE = OUTPUT_DIR / "features_course_certs.csv"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Controlled manipulation categories and targets
TARGET_COUNTS = {
    "genuine": 1500,
    "name_changed": 300,
    "certificate_id_changed": 300,
    "date_changed": 300,
    "course_changed": 300,
    "grade_changed": 300,
    "logo_changed": 200,
    "seal_changed": 200,
    "signature_changed": 200,
    "qr_replaced": 300,
    "qr_copied": 300,
    "multiple_fields": 500,
}

ISSUERS = [
    ("Coursera", "coursera.org"),
    ("edX", "edx.org"),
    ("Udemy", "udemy.com"),
    ("Harvard Online", "harvard.edu"),
    ("Stanford Online", "stanford.edu"),
    ("Credly", "credly.com"),
    ("Microsoft Learn", "microsoft.com"),
    ("Google Cloud", "cloud.google.com"),
]

COURSES = [
    "Machine Learning Specialization",
    "Deep Learning Specialization",
    "Full-Stack Web Development Bootcamp",
    "Cloud Architecture on AWS",
    "Data Science Professional Certificate",
    "Cybersecurity Fundamentals",
    "Applied Data Science with Python",
    "DevOps and Software Engineering",
]

NAMES = [
    "Alice Johnson",
    "Bob Smith",
    "Charlie Davis",
    "Diana Prince",
    "Ethan Hunt",
    "Fiona Gallagher",
    "George Miller",
    "Hannah Abbott",
    "Ian Wright",
    "Julia Roberts",
    "Kevin Bacon",
    "Laura Croft",
]


def ensure_directories() -> None:
    """Create all subdirectories under dataset/course_certificates/."""
    for category in TARGET_COUNTS.keys():
        if category == "genuine":
            p = OUTPUT_DIR / "genuine"
        else:
            p = OUTPUT_DIR / "tampered" / category
        p.mkdir(parents=True, exist_ok=True)


def generate_dataset() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Generate synthetic course certificate metadata and cross-modal feature distributions."""
    random.seed(42)
    np.random.seed(42)

    metadata_rows: list[dict[str, Any]] = []
    feature_rows: list[dict[str, Any]] = []

    num_templates = 50
    # Group templates into train (70%), val (15%), test (15%)
    template_ids = [f"TPL_{i:03d}" for i in range(num_templates)]
    random.shuffle(template_ids)

    n_train = int(0.70 * num_templates)
    n_val = int(0.15 * num_templates)

    train_tpls = set(template_ids[:n_train])
    val_tpls = set(template_ids[n_train : n_train + n_val])
    test_tpls = set(template_ids[n_train + n_val :])

    sample_id = 0

    for category, count in TARGET_COUNTS.items():
        is_genuine = category == "genuine"

        for _ in range(count):
            sample_id += 1
            image_id = f"CERT_{sample_id:05d}"
            tpl_id = random.choice(template_ids)

            if tpl_id in train_tpls:
                split = "train"
            elif tpl_id in val_tpls:
                split = "val"
            else:
                split = "test"

            issuer_name, domain = random.choice(ISSUERS)
            course = random.choice(COURSES)
            name = random.choice(NAMES)
            cert_id = f"UC-{random.randint(10000000, 99999999)}"

            # Default parameters for genuine
            qr_present = True
            qr_valid = True
            online_match = True
            copied_qr = False
            field_changed = "none"
            authenticity = 1  # 1 = Authentic, 0 = Tampered

            # Default feature distributions (genuine)
            ocr_confidence = float(np.clip(np.random.normal(0.92, 0.04), 0.75, 0.99))
            tampering_prob = float(np.clip(np.random.normal(0.08, 0.05), 0.01, 0.25))
            qr_detected = 1
            qr_decoded = 1
            url_valid_syntax = 1
            issuer_trusted = 1
            domain_match = 1
            online_available = 1
            name_match_score = float(np.clip(np.random.normal(0.96, 0.03), 0.85, 1.0))
            course_match_score = float(np.clip(np.random.normal(0.94, 0.04), 0.82, 1.0))
            cert_id_match_score = float(np.clip(np.random.normal(0.98, 0.02), 0.90, 1.0))
            date_match_score = float(np.clip(np.random.normal(0.95, 0.03), 0.85, 1.0))
            signature_score = float(np.clip(np.random.normal(0.85, 0.08), 0.50, 1.0))
            seal_score = float(np.clip(np.random.normal(0.82, 0.09), 0.40, 1.0))

            # Modify signals based on tamper category
            if not is_genuine:
                authenticity = 0
                field_changed = category

                if category == "name_changed":
                    name_match_score = float(np.clip(np.random.normal(0.20, 0.10), 0.0, 0.45))
                    tampering_prob = float(np.clip(np.random.normal(0.68, 0.12), 0.40, 0.95))
                    online_match = False

                elif category == "certificate_id_changed":
                    cert_id_match_score = float(np.clip(np.random.normal(0.15, 0.08), 0.0, 0.35))
                    tampering_prob = float(np.clip(np.random.normal(0.72, 0.10), 0.45, 0.95))
                    online_match = False

                elif category == "date_changed":
                    date_match_score = float(np.clip(np.random.normal(0.25, 0.10), 0.0, 0.50))
                    tampering_prob = float(np.clip(np.random.normal(0.65, 0.12), 0.35, 0.90))

                elif category == "course_changed":
                    course_match_score = float(np.clip(np.random.normal(0.22, 0.10), 0.0, 0.45))
                    tampering_prob = float(np.clip(np.random.normal(0.70, 0.10), 0.40, 0.92))
                    online_match = False

                elif category == "grade_changed":
                    tampering_prob = float(np.clip(np.random.normal(0.64, 0.12), 0.35, 0.90))

                elif category == "logo_changed":
                    tampering_prob = float(np.clip(np.random.normal(0.75, 0.10), 0.50, 0.96))
                    domain_match = random.choice([0, 1])

                elif category == "seal_changed":
                    seal_score = float(np.clip(np.random.normal(0.18, 0.08), 0.0, 0.35))
                    tampering_prob = float(np.clip(np.random.normal(0.66, 0.12), 0.38, 0.92))

                elif category == "signature_changed":
                    signature_score = float(np.clip(np.random.normal(0.20, 0.10), 0.0, 0.40))
                    tampering_prob = float(np.clip(np.random.normal(0.68, 0.10), 0.42, 0.92))

                elif category == "qr_replaced":
                    qr_valid = False
                    url_valid_syntax = random.choice([0, 1])
                    issuer_trusted = 0
                    domain_match = 0
                    online_available = 0
                    name_match_score = 0.0
                    cert_id_match_score = 0.0
                    course_match_score = 0.0
                    date_match_score = 0.0
                    tampering_prob = float(np.clip(np.random.normal(0.78, 0.09), 0.55, 0.98))

                elif category == "qr_copied":
                    # Critical Copied QR attack: Valid QR resolves to genuine cert of someone else!
                    qr_valid = True
                    copied_qr = True
                    online_available = 1
                    name_match_score = float(np.clip(np.random.normal(0.18, 0.08), 0.0, 0.35))
                    cert_id_match_score = float(np.clip(np.random.normal(0.15, 0.08), 0.0, 0.30))
                    tampering_prob = float(np.clip(np.random.normal(0.45, 0.15), 0.20, 0.80))
                    online_match = False

                elif category == "multiple_fields":
                    name_match_score = float(np.clip(np.random.normal(0.15, 0.08), 0.0, 0.30))
                    cert_id_match_score = float(np.clip(np.random.normal(0.12, 0.06), 0.0, 0.25))
                    date_match_score = float(np.clip(np.random.normal(0.20, 0.08), 0.0, 0.40))
                    tampering_prob = float(np.clip(np.random.normal(0.85, 0.08), 0.65, 0.99))
                    online_match = False

            # Append metadata
            metadata_rows.append(
                {
                    "image_id": image_id,
                    "template_id": tpl_id,
                    "split": split,
                    "authenticity": authenticity,
                    "tamper_type": category,
                    "field_changed": field_changed,
                    "qr_present": int(qr_present),
                    "qr_valid": int(qr_valid),
                    "online_match": int(online_match),
                    "copied_qr": int(copied_qr),
                    "candidate_name": name,
                    "course_name": course,
                    "certificate_id": cert_id,
                    "issuer": issuer_name,
                }
            )

            # Append 14-D features for ML training
            feature_rows.append(
                {
                    "image_id": image_id,
                    "split": split,
                    "authenticity": authenticity,
                    "ocr_confidence": round(ocr_confidence, 4),
                    "tampering_probability": round(tampering_prob, 4),
                    "qr_detected": qr_detected,
                    "qr_decoded": qr_decoded,
                    "url_valid_syntax": url_valid_syntax,
                    "issuer_trusted": issuer_trusted,
                    "domain_match": domain_match,
                    "online_available": online_available,
                    "name_match_score": round(name_match_score, 4),
                    "course_match_score": round(course_match_score, 4),
                    "cert_id_match_score": round(cert_id_match_score, 4),
                    "date_match_score": round(date_match_score, 4),
                    "signature_score": round(signature_score, 4),
                    "seal_score": round(seal_score, 4),
                }
            )

    return metadata_rows, feature_rows


def save_csv(data: list[dict[str, Any]], filepath: Path) -> None:
    """Save rows into CSV file."""
    if not data:
        return
    fieldnames = list(data[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    logger.info("Saved %d records to %s", len(data), filepath)


def main() -> None:
    ensure_directories()
    metadata, features = generate_dataset()
    save_csv(metadata, METADATA_FILE)
    save_csv(features, FEATURES_FILE)

    total_samples = len(metadata)
    genuine_samples = sum(1 for m in metadata if m["authenticity"] == 1)
    tampered_samples = total_samples - genuine_samples

    print("\n" + "=" * 70)
    print("CUSTOM COURSE CERTIFICATE DATASET GENERATION REPORT")
    print("=" * 70)
    print(f"Total Certificate Samples: {total_samples}")
    print(f"  - Genuine Samples:       {genuine_samples} (100% genuine specimens)")
    print(f"  - Tampered Samples:      {tampered_samples} across 11 tampering categories")
    for cat, count in TARGET_COUNTS.items():
        if cat != "genuine":
            print(f"    * {cat}: {count} samples")
    print(f"Metadata File: {METADATA_FILE}")
    print(f"Features File: {FEATURES_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
