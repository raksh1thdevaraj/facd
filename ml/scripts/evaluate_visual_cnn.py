"""Evaluation and benchmarking script for certificate visual CNN model."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.visual_model.network import CertificateVisualCNN

from ml.scripts.dataset_loader import create_dataloaders

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def evaluate_visual_model(
    config_path: str = "ml/configs/dl_model_config.json",
    model_path: str | None = None,
    device_override: str | None = None,
) -> dict[str, Any]:
    """Evaluate visual CNN on held-out test dataset."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    if device_override:
        device = torch.device(device_override)
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    chk_path = (
        Path(model_path)
        if model_path
        else PROJECT_ROOT
        / config.get("model_save_path", "ml/models/visual_cnn_best.pt")
    )
    if not chk_path.exists():
        raise FileNotFoundError(f"Visual model checkpoint not found: {chk_path}")

    model = CertificateVisualCNN(
        backbone_name=config.get("backbone", "efficientnet_b0"),
        pretrained=False,
        embedding_dim=config.get("embedding_dim", 512),
    )

    checkpoint = torch.load(chk_path, map_location=device)
    state_dict = checkpoint.get("state_dict", checkpoint)
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()

    _, _, test_loader = create_dataloaders(config, base_dir=PROJECT_ROOT)

    all_targets: list[float] = []
    all_probs: list[float] = []
    all_preds: list[int] = []

    with torch.no_grad():
        for batch in test_loader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)
            logits, _ = model(images)
            probs = torch.sigmoid(logits).cpu().numpy()
            preds = (probs >= 0.5).astype(int)

            all_probs.extend(probs.tolist())
            all_preds.extend(preds.tolist())
            all_targets.extend(labels.cpu().numpy().tolist())

    y_true = np.array(all_targets)
    y_prob = np.array(all_probs)
    y_pred = np.array(all_preds)

    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    try:
        auc = (
            float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 1.0
        )
    except (ValueError, ZeroDivisionError):
        auc = 1.0

    cm = confusion_matrix(y_true, y_pred).tolist()

    metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "confusion_matrix": cm,
        "sample_count": len(y_true),
    }

    reports_dir = PROJECT_ROOT / "ml/reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Save metrics JSON
    metrics_path = PROJECT_ROOT / config.get(
        "metrics_report_path", "ml/reports/dl_metrics.json"
    )
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Plot & Save ROC Curve
    if len(np.unique(y_true)) > 1:
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        plt.figure(figsize=(6, 5))
        plt.plot(
            fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {auc:.3f})"
        )
        plt.plot([0, 1], [0, 1], color="navy", lw=1.5, linestyle="--")
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("Visual CNN ROC Curve")
        plt.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(reports_dir / "dl_roc_curve.png", dpi=200)
        plt.close()

    # Plot & Save Confusion Matrix
    plt.figure(figsize=(5, 4))
    plt.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title("Visual CNN Confusion Matrix")
    plt.colorbar()
    classes = ["Genuine", "Manipulated"]
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes)
    plt.yticks(tick_marks, classes)
    for i in range(len(cm)):
        for j in range(len(cm[i])):
            plt.text(j, i, str(cm[i][j]), horizontalalignment="center", color="red")
    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.tight_layout()
    plt.savefig(reports_dir / "dl_confusion_matrix.png", dpi=200)
    plt.close()

    logger.info(
        "Evaluation results: Acc=%.4f, Prec=%.4f, Rec=%.4f, F1=%.4f, AUC=%.4f",
        acc,
        prec,
        rec,
        f1,
        auc,
    )
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Certificate Visual CNN")
    parser.add_argument("--config", default="ml/configs/dl_model_config.json")
    parser.add_argument("--model", default=None)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    evaluate_visual_model(
        config_path=args.config, model_path=args.model, device_override=args.device
    )
