"""Benchmark multimodal fusion strategies against held-out test dataset."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.score_fusion.early_fusion import MultimodalFusionMLP
from app.modules.score_fusion.late_fusion import WeightedLateFusion
from app.modules.score_fusion.meta_classifier import StackingMetaClassifier

from ml.scripts.train_early_fusion_mlp import generate_multimodal_features
from ml.scripts.train_meta_classifier import extract_meta_features_from_csv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def evaluate_multimodal_models() -> dict[str, Any]:
    """Evaluate Early, Late, and Stacking Fusion methods on test dataset."""
    test_csv = PROJECT_ROOT / "ml/data/features_test.csv"
    if not test_csv.exists():
        raise FileNotFoundError(f"Test dataset not found at {test_csv}")

    results: dict[str, Any] = {}

    # 1. Evaluate Late Fusion Weighted Blender
    X_meta, y_auth = extract_meta_features_from_csv(test_csv)
    blender = WeightedLateFusion()
    late_preds: list[int] = []
    late_scores: list[float] = []

    for i in range(len(y_auth)):
        s_auth, _, _, _ = blender.blend(
            visual_fake_prob=float(X_meta[i, 0]),
            tabular_fake_prob=float(X_meta[i, 1]),
            forensic_score=float(X_meta[i, 2]),
            text_consistency_score=float(X_meta[i, 3]),
            template_score=float(X_meta[i, 4]),
        )
        late_scores.append(s_auth)
        # Authentic if score >= 0.60 (or threshold 0.5 for binary evaluation)
        late_preds.append(1 if s_auth >= 0.50 else 0)

    acc_late = float(accuracy_score(y_auth, late_preds))
    f1_late = float(f1_score(y_auth, late_preds, zero_division=0))
    prec_late = float(precision_score(y_auth, late_preds, zero_division=0))
    rec_late = float(recall_score(y_auth, late_preds, zero_division=0))
    auc_late = (
        float(roc_auc_score(y_auth, late_scores)) if len(np.unique(y_auth)) > 1 else 1.0
    )

    results["late_fusion"] = {
        "accuracy": round(acc_late, 4),
        "f1_score": round(f1_late, 4),
        "precision": round(prec_late, 4),
        "recall": round(rec_late, 4),
        "roc_auc": round(auc_late, 4),
    }

    # 2. Evaluate Stacking Meta-Classifier
    meta_model_path = PROJECT_ROOT / "ml/models/meta_classifier.joblib"
    meta_clf = StackingMetaClassifier(
        model_path=meta_model_path if meta_model_path.exists() else None
    )
    stack_scores: list[float] = []
    stack_preds: list[int] = []

    for i in range(len(y_auth)):
        s_meta = meta_clf.predict_authenticity(X_meta[i])
        stack_scores.append(s_meta)
        stack_preds.append(1 if s_meta >= 0.50 else 0)

    acc_stack = float(accuracy_score(y_auth, stack_preds))
    f1_stack = float(f1_score(y_auth, stack_preds, zero_division=0))
    prec_stack = float(precision_score(y_auth, stack_preds, zero_division=0))
    rec_stack = float(recall_score(y_auth, stack_preds, zero_division=0))
    auc_stack = (
        float(roc_auc_score(y_auth, stack_scores))
        if len(np.unique(y_auth)) > 1
        else 1.0
    )

    results["stacking_meta_classifier"] = {
        "accuracy": round(acc_stack, 4),
        "f1_score": round(f1_stack, 4),
        "precision": round(prec_stack, 4),
        "recall": round(rec_stack, 4),
        "roc_auc": round(auc_stack, 4),
    }

    # 3. Evaluate Early Fusion MLP (if artifact exists)
    early_mlp_path = PROJECT_ROOT / "ml/models/multimodal_fusion_mlp.pt"
    if early_mlp_path.exists():
        X_fused, _y_fused_fake = generate_multimodal_features(test_csv, seed=999)
        early_mlp = MultimodalFusionMLP()
        chk = torch.load(early_mlp_path, map_location="cpu")
        early_mlp.load_state_dict(chk.get("state_dict", chk))
        early_mlp.eval()

        mlp_preds: list[int] = []
        mlp_scores: list[float] = []
        with torch.no_grad():
            tensor = torch.from_numpy(X_fused).float()
            probs = torch.sigmoid(early_mlp(tensor)).cpu().numpy()
            for p in probs:
                mlp_scores.append(float(1.0 - p))
                mlp_preds.append(0 if p >= 0.50 else 1)

        acc_early = float(accuracy_score(y_auth, mlp_preds))
        f1_early = float(f1_score(y_auth, mlp_preds, zero_division=0))
        prec_early = float(precision_score(y_auth, mlp_preds, zero_division=0))
        rec_early = float(recall_score(y_auth, mlp_preds, zero_division=0))
        auc_early = (
            float(roc_auc_score(y_auth, mlp_scores))
            if len(np.unique(y_auth)) > 1
            else 1.0
        )

        results["early_fusion_mlp"] = {
            "accuracy": round(acc_early, 4),
            "f1_score": round(f1_early, 4),
            "precision": round(prec_early, 4),
            "recall": round(rec_early, 4),
            "roc_auc": round(auc_early, 4),
        }

    # Save to ml/reports/multimodal_metrics.json
    report_file = PROJECT_ROOT / "ml/reports/multimodal_metrics.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info("Multimodal evaluation complete:\n%s", json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    evaluate_multimodal_models()
