"""Publication-Grade Evaluation Charts & Visualizations (CHIP TST-08).

Renders publication-grade, high-resolution (300 DPI) visualization figures for inclusion
in academic papers, project documentation, and thesis defense reports:
1. Confusion Matrix Heatmap (ml/reports/evaluation_confusion_matrix.png)
2. Comparative ROC Curves Plot (ml/reports/comparative_roc_curves.png)
3. Precision-Recall Curves Plot (ml/reports/precision_recall_curves.png)
4. Forgery Category Breakdown Bar Chart (ml/reports/category_breakdown.png)
5. Feature Ablation Study Impact Chart (ml/reports/ablation_study_chart.png)
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, cast

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_recall_curve, roc_curve

logger = logging.getLogger(__name__)

REPORTS_DIR = PROJECT_ROOT / "ml" / "reports"


def generate_confusion_matrix_chart(
    cm_dict: dict[str, int],
    output_path: Path | None = None,
    dpi: int = 300,
) -> Path:
    """Generate publication-grade confusion matrix heatmap."""
    target_path = output_path or (REPORTS_DIR / "evaluation_confusion_matrix.png")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    tn = cm_dict.get("true_negatives", 0)
    fp = cm_dict.get("false_positives", 0)
    fn = cm_dict.get("false_negatives", 0)
    tp = cm_dict.get("true_positives", 0)

    matrix = np.array([[tn, fp], [fn, tp]])
    total = np.sum(matrix)
    normalized = matrix / total if total > 0 else matrix

    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=dpi)
    cax = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
    fig.colorbar(cax, ax=ax, fraction=0.046, pad=0.04)

    classes = ["Genuine (0)", "Manipulated (1)"]
    tick_marks = np.arange(len(classes))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(classes, fontsize=11, fontweight="medium")
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(classes, fontsize=11, fontweight="medium")

    thresh = matrix.max() / 2.0
    labels = [
        [
            f"TN\n{tn}\n({normalized[0, 0] * 100:.1f}%)",
            f"FP\n{fp}\n({normalized[0, 1] * 100:.1f}%)",
        ],
        [
            f"FN\n{fn}\n({normalized[1, 0] * 100:.1f}%)",
            f"TP\n{tp}\n({normalized[1, 1] * 100:.1f}%)",
        ],
    ]

    for i in range(2):
        for j in range(2):
            color = "white" if matrix[i, j] > thresh else "#1a202c"
            ax.text(
                j,
                i,
                labels[i][j],
                ha="center",
                va="center",
                color=color,
                fontsize=12,
                fontweight="bold",
            )

    ax.set_ylabel("Ground Truth Class", fontsize=12, fontweight="bold", labelpad=10)
    ax.set_xlabel("Predicted Class", fontsize=12, fontweight="bold", labelpad=10)
    ax.set_title(
        "Normalized Confusion Matrix (Multimodal Fusion)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    plt.tight_layout()

    fig.savefig(target_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved confusion matrix chart to %s", target_path)
    return target_path


def generate_comparative_roc_chart(
    predictions: list[dict[str, Any]],
    output_path: Path | None = None,
    dpi: int = 300,
) -> Path:
    """Generate overlaid ROC curves for Baseline, Visual CNN, and Multimodal models."""
    target_path = output_path or (REPORTS_DIR / "comparative_roc_curves.png")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    y_true: Any = np.array([p["ground_truth"] for p in predictions])
    base_prob: Any = np.array([p["baseline_prob"] for p in predictions])
    vis_prob: Any = np.array([p["visual_prob"] for p in predictions])
    multi_prob: Any = np.array([p["multimodal_prob"] for p in predictions])

    fig, ax = plt.subplots(figsize=(7, 6), dpi=dpi)

    models = [
        ("Baseline Tabular ML", base_prob, "#4299e1", "--"),
        ("Visual CNN (EfficientNet-B0)", vis_prob, "#ed8936", "-."),
        ("Multimodal Fusion (Proposed)", multi_prob, "#38a169", "-"),
    ]

    for name, probs, color, style in models:
        fpr: Any
        tpr: Any
        fpr, tpr, _ = roc_curve(y_true, probs)
        from sklearn.metrics import roc_auc_score

        auc = roc_auc_score(y_true, probs)
        cast(Any, ax).plot(
            fpr,
            tpr,
            label=f"{name} (AUC = {auc:.4f})",
            color=color,
            linestyle=style,
            linewidth=2.4,
        )

    # Random guess diagonal
    ax.plot(
        [0, 1],
        [0, 1],
        color="#a0aec0",
        linestyle=":",
        linewidth=1.5,
        label="Random Guess (AUC = 0.5000)",
    )

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel(
        "False Positive Rate (1 - Specificity)", fontsize=11, fontweight="bold"
    )
    ax.set_ylabel(
        "True Positive Rate (Sensitivity / Recall)", fontsize=11, fontweight="bold"
    )
    ax.set_title(
        "Comparative Receiver Operating Characteristic (ROC)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(
        loc="lower right",
        frameon=True,
        facecolor="white",
        edgecolor="#cbd5e0",
        fontsize=10,
    )
    plt.tight_layout()

    fig.savefig(target_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved comparative ROC chart to %s", target_path)
    return target_path


def generate_precision_recall_chart(
    predictions: list[dict[str, Any]],
    output_path: Path | None = None,
    dpi: int = 300,
) -> Path:
    """Generate overlaid Precision-Recall curves."""
    target_path = output_path or (REPORTS_DIR / "precision_recall_curves.png")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    y_true: Any = np.array([p["ground_truth"] for p in predictions])
    base_prob: Any = np.array([p["baseline_prob"] for p in predictions])
    vis_prob: Any = np.array([p["visual_prob"] for p in predictions])
    multi_prob: Any = np.array([p["multimodal_prob"] for p in predictions])

    fig, ax = plt.subplots(figsize=(7, 6), dpi=dpi)

    models = [
        ("Baseline Tabular ML", base_prob, "#4299e1", "--"),
        ("Visual CNN", vis_prob, "#ed8936", "-."),
        ("Multimodal Fusion (Proposed)", multi_prob, "#38a169", "-"),
    ]

    for name, probs, color, style in models:
        prec: Any
        rec: Any
        prec, rec, _ = precision_recall_curve(y_true, probs)
        from sklearn.metrics import average_precision_score

        ap = average_precision_score(y_true, probs)
        cast(Any, ax).plot(
            rec,
            prec,
            label=f"{name} (PR-AUC = {ap:.4f})",
            color=color,
            linestyle=style,
            linewidth=2.4,
        )

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Recall (Sensitivity)", fontsize=11, fontweight="bold")
    ax.set_ylabel(
        "Precision (Positive Predictive Value)", fontsize=11, fontweight="bold"
    )
    ax.set_title(
        "Comparative Precision-Recall Curves", fontsize=13, fontweight="bold", pad=15
    )
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(
        loc="lower left",
        frameon=True,
        facecolor="white",
        edgecolor="#cbd5e0",
        fontsize=10,
    )
    plt.tight_layout()

    fig.savefig(target_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved PR curves chart to %s", target_path)
    return target_path


def generate_category_breakdown_chart(
    category_results: dict[str, Any],
    output_path: Path | None = None,
    dpi: int = 300,
) -> Path:
    """Generate bar chart displaying detection rates across the 5 forgery categories."""
    target_path = output_path or (REPORTS_DIR / "category_breakdown.png")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    categories = list(category_results["categories"].keys())
    rates = [
        category_results["categories"][c]["detection_rate"] * 100 for c in categories
    ]

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=dpi)
    colors = ["#2b6cb0", "#319795", "#d69e2e", "#dd6b20", "#38a169"]
    bars = ax.bar(
        categories, rates, color=colors, width=0.55, edgecolor="#2d3748", linewidth=1.2
    )

    ax.set_ylim(0.0, 110.0)
    ax.set_ylabel("Detection Sensitivity / Recall (%)", fontsize=11, fontweight="bold")
    ax.set_title(
        "Detection Sensitivity by Forgery Category (FR-TST-04)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )
    ax.axhline(
        90.0,
        color="#e53e3e",
        linestyle="--",
        linewidth=1.5,
        label="Target Performance (>= 90%)",
    )

    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            h + 2.0,
            f"{h:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.xticks(rotation=15, ha="right", fontsize=10, fontweight="medium")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#cbd5e0")
    plt.tight_layout()

    fig.savefig(target_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved category breakdown chart to %s", target_path)
    return target_path


def generate_ablation_chart(
    ablation_results: list[dict[str, Any]],
    output_path: Path | None = None,
    dpi: int = 300,
) -> Path:
    """Generate bar chart showing F1 score impact (Delta F1) for each removed component."""
    target_path = output_path or (REPORTS_DIR / "ablation_study_chart.png")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Exclude full_system from the delta chart
    ablated = [r for r in ablation_results if r["config_id"] != "full_system"]
    names = [r["disabled_module"] for r in ablated]
    deltas = [
        abs(r.get("delta_f1_pct", r.get("delta_f1_percentage", 0.0))) for r in ablated
    ]

    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=dpi)
    y_pos = np.arange(len(names))
    bars = ax.barh(
        y_pos, deltas, color="#e53e3e", alpha=0.85, edgecolor="#742a2a", height=0.55
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10, fontweight="medium")
    ax.invert_yaxis()  # top-down order
    ax.set_xlabel(
        "F1-Score Degradation when Module Removed (-Delta F1 %)",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_title(
        "Ablation Study: Empirical Importance of Subsystems (FR-TST-06)",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )

    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + 0.2,
            bar.get_y() + bar.get_height() / 2.0,
            f"-{w:.1f}%",
            ha="left",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="#9b2c2c",
        )

    ax.set_xlim(0.0, float(max(deltas) + 2.5))
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()

    fig.savefig(target_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved ablation chart to %s", target_path)
    return target_path


def generate_all_evaluation_charts(
    predictions_path: Path | None = None,
    metrics: dict[str, Any] | None = None,
    categories: dict[str, Any] | None = None,
    ablation: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Execute end-to-end rendering pipeline for all 5 evaluation figures."""
    pred_path = predictions_path or (REPORTS_DIR / "raw_test_predictions.json")
    with open(pred_path, "r", encoding="utf-8") as f:
        predictions = json.load(f)

    results: dict[str, Path] = {}
    if metrics and "confusion_matrix" in metrics:
        results["confusion_matrix"] = generate_confusion_matrix_chart(
            metrics["confusion_matrix"]
        )

    results["comparative_roc"] = generate_comparative_roc_chart(predictions)
    results["precision_recall"] = generate_precision_recall_chart(predictions)

    if categories:
        results["category_breakdown"] = generate_category_breakdown_chart(categories)

    ab_list = None
    if ablation:
        if isinstance(ablation, list):
            ab_list = ablation
        elif "results" in ablation:
            ab_list = ablation["results"]
        elif "configurations" in ablation:
            ab_list = ablation["configurations"]

    if ab_list:
        results["ablation_chart"] = generate_ablation_chart(ab_list)

    return results


def generate_all_charts(
    benchmark_predictions: list[dict[str, Any]],
    comparison_data: dict[str, Any] | None = None,
    category_data: dict[str, Any] | None = None,
    ablation_data: dict[str, Any] | None = None,
    output_dir: Path | None = None,
) -> dict[str, str]:
    """Helper for generating all charts directly from in-memory predictions and data."""
    out_dir = output_dir or REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    res: dict[str, str] = {}

    y_true = np.array([p["ground_truth"] for p in benchmark_predictions])
    y_pred = np.array([p["predicted_label"] for p in benchmark_predictions])
    y_prob = np.array([p["multimodal_prob"] for p in benchmark_predictions])
    from ml.evaluation.metric_calculator import calculate_metrics

    metrics = calculate_metrics(y_true, y_pred, y_prob)

    res["confusion_matrix"] = str(
        generate_confusion_matrix_chart(
            metrics["confusion_matrix"],
            output_path=out_dir / "evaluation_confusion_matrix.png",
        )
    )
    res["comparative_roc"] = str(
        generate_comparative_roc_chart(
            benchmark_predictions, output_path=out_dir / "comparative_roc_curves.png"
        )
    )
    res["precision_recall"] = str(
        generate_precision_recall_chart(
            benchmark_predictions, output_path=out_dir / "precision_recall_curves.png"
        )
    )

    if category_data:
        res["category_breakdown"] = str(
            generate_category_breakdown_chart(
                category_data, output_path=out_dir / "category_breakdown.png"
            )
        )

    if ablation_data:
        ab_list = (
            ablation_data
            if isinstance(ablation_data, list)
            else ablation_data.get("configurations", ablation_data.get("results", []))
        )
        if ab_list:
            res["ablation_chart"] = str(
                generate_ablation_chart(
                    ab_list, output_path=out_dir / "ablation_study_chart.png"
                )
            )

    return res


if __name__ == "__main__":
    from ml.evaluation.ablation_runner import run_ablation_study
    from ml.evaluation.category_evaluator import evaluate_categories
    from ml.evaluation.metric_calculator import calculate_metrics

    pred_file = REPORTS_DIR / "raw_test_predictions.json"
    with open(pred_file, "r", encoding="utf-8") as f:
        preds = json.load(f)

    y_t = np.array([p["ground_truth"] for p in preds])
    m_p = np.array([p["multimodal_prob"] for p in preds])
    p_l = np.array([p["predicted_label"] for p in preds])

    calc_metrics = calculate_metrics(y_t, p_l, m_p)
    cat_eval = evaluate_categories(preds)
    abl_eval = run_ablation_study(preds)

    charts = generate_all_evaluation_charts(
        predictions_path=pred_file,
        metrics=calc_metrics,
        categories=cat_eval,
        ablation=abl_eval,
    )
    print("Generated all 5 evaluation charts:", list(charts.keys()))
