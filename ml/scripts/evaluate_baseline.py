import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from ml.scripts.extract_dataset_features import generate_synthetic_feature_dataset
from ml.scripts.preprocess_features import FEATURE_NAMES, TabularDataPreprocessor


def evaluate_baseline_model(
    model_path: Path | None = None,
    scaler_path: Path | None = None,
    test_df: pd.DataFrame | None = None,
    reports_dir: Path | None = None,
) -> dict[str, Any]:
    """Evaluate trained model on held-out test set, generating metrics and diagnostic plots.

    Args:
        model_path: Path to serialized estimator joblib.
        scaler_path: Path to serialized feature scaler joblib.
        test_df: Held-out test DataFrame.
        reports_dir: Directory to save evaluation reports and plots.

    Returns:
        Dictionary of comprehensive evaluation metrics.
    """
    rep_dir = reports_dir or Path("ml/reports")
    rep_dir.mkdir(parents=True, exist_ok=True)

    m_path = model_path or Path("ml/models/baseline_model_v1.joblib")
    model = joblib.load(str(m_path))

    if test_df is None:
        _, _, test_df = generate_synthetic_feature_dataset(
            n_samples=600, random_state=42
        )

    X_test = test_df[FEATURE_NAMES].values.astype(np.float32)
    y_test = test_df["is_manipulated"].values.astype(int)

    # If linear/SVM model, scale features
    model_class_name = model.__class__.__name__
    if (
        model_class_name in ("LogisticRegression", "SVC")
        and scaler_path
        and Path(scaler_path).exists()
    ):
        preprocessor = TabularDataPreprocessor.load(scaler_path)
        X_test_eval = preprocessor.transform(X_test)
    else:
        X_test_eval = X_test

    # Predictions
    y_pred = model.predict(X_test_eval)
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test_eval)[:, 1]
    else:
        y_prob = y_pred.astype(float)

    # Calculate metrics
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "model_name": model_class_name,
        "test_samples": len(y_test),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "confusion_matrix": {
            "true_negatives": cm[0][0],
            "false_positives": cm[0][1],
            "false_negatives": cm[1][0],
            "true_positives": cm[1][1],
        },
        "meets_specification": acc >= 0.85 and f1 >= 0.85,
    }

    # Save metrics JSON
    metrics_path = rep_dir / "baseline_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # 1. Plot Confusion Matrix
    fig, ax = plt.subplots(figsize=(5, 4))
    cax = ax.matshow(cm, cmap="Blues", alpha=0.8)
    fig.colorbar(cax)
    for i in range(2):
        for j in range(2):
            ax.text(
                j,
                i,
                str(cm[i][j]),
                va="center",
                ha="center",
                fontsize=14,
                fontweight="bold",
                color="black",
            )
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Genuine", "Manipulated"])
    ax.set_yticklabels(["Genuine", "Manipulated"])
    ax.set_xlabel("Predicted Label", fontweight="bold")
    ax.set_ylabel("True Label", fontweight="bold")
    ax.set_title("Baseline Confusion Matrix", pad=20, fontweight="bold")
    plt.tight_layout()
    cm_path = rep_dir / "baseline_confusion_matrix.png"
    plt.savefig(cm_path, dpi=200)
    plt.close(fig)

    # 2. Plot ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color="#1f77b4", lw=2.5, label=f"ROC Curve (AUC = {roc_auc:.3f})")
    ax.plot([0, 1], [0, 1], color="grey", linestyle="--", lw=1.5)
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("False Positive Rate (1 - Specificity)", fontweight="bold")
    ax.set_ylabel("True Positive Rate (Sensitivity)", fontweight="bold")
    ax.set_title("Receiver Operating Characteristic (ROC)", fontweight="bold")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    roc_path = rep_dir / "baseline_roc_curve.png"
    plt.savefig(roc_path, dpi=200)
    plt.close(fig)

    return metrics


if __name__ == "__main__":
    res = evaluate_baseline_model()
    print("Evaluation Results:")
    print(json.dumps(res, indent=2))
