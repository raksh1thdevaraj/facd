"""Model export and manifest generation script for Phase 09 ML Baseline (CHIP MOD-09).

Generates model_manifest.json containing version metadata, feature names, hyperparams,
performance benchmarks, and file checksums for production deployment.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ml.scripts.preprocess_features import FEATURE_NAMES

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = ROOT_DIR / "ml" / "models"
REPORTS_DIR = ROOT_DIR / "ml" / "reports"


def compute_sha256(filepath: Path) -> str:
    """Compute sha256 checksum of a file."""
    if not filepath.exists():
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_manifest(
    model_version: str = "1.0.0",
    models_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> dict[str, Any]:
    """Generate production model manifest JSON."""
    m_dir = models_dir or MODELS_DIR
    r_dir = reports_dir or REPORTS_DIR

    model_path = m_dir / "baseline_model_v1.joblib"
    scaler_path = m_dir / "feature_scaler.joblib"
    metrics_path = r_dir / "baseline_metrics.json"

    metrics: dict[str, Any] = {}
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)

    manifest = {
        "model_name": "academic_certificate_fake_detector_baseline",
        "model_version": model_version,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "framework": "scikit-learn",
        "model_type": metrics.get("model_name", "RandomForestClassifier"),
        "feature_count": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "evaluation_metrics": {
            "test_accuracy": metrics.get("accuracy", metrics.get("test_accuracy", 0.0)),
            "test_f1_score": metrics.get("f1_score", metrics.get("test_f1_score", 0.0)),
            "test_precision": metrics.get(
                "precision", metrics.get("test_precision", 0.0)
            ),
            "test_recall": metrics.get("recall", metrics.get("test_recall", 0.0)),
            "test_roc_auc": metrics.get("roc_auc", metrics.get("test_roc_auc", 0.0)),
        },
        "artifacts": {
            "model_file": model_path.name,
            "model_sha256": compute_sha256(model_path),
            "scaler_file": scaler_path.name if scaler_path.exists() else None,
            "scaler_sha256": compute_sha256(scaler_path)
            if scaler_path.exists()
            else None,
        },
        "inference_spec": {
            "input_dimension": 22,
            "classes": ["authentic", "manipulated"],
            "threshold": 0.5,
            "target_latency_ms": 20.0,
        },
    }

    manifest_file = m_dir / "model_manifest.json"
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info("Exported model manifest to %s", manifest_file)
    return manifest


if __name__ == "__main__":
    generate_manifest()
