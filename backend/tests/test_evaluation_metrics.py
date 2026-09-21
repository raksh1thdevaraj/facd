"""Unit & Benchmark Evaluation Metrics Test Suite (Phase 19 - CHIP TST-11).

Formally asserts that the multimodal academic certificate verification system satisfies:
- TC-EVAL-01: Full evaluation suite execution on held-out test split
- TC-EVAL-02: Quantitative metrics assertion (Overall Accuracy >= 92%, F1 >= 0.92 - NFR-01)
- FR-TST-03: Comprehensive classification metrics (Acc, Prec, Rec, F1, ROC-AUC)
- FR-TST-04: Per-category forgery sensitivity breakdown (>= 85% across all 5 categories)
- FR-TST-05: Superiority of Multimodal Fusion over individual single-branch models
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from ml.evaluation.benchmark_runner import BenchmarkRunner
from ml.evaluation.category_evaluator import FORGERY_CATEGORIES, evaluate_categories
from ml.evaluation.metric_calculator import calculate_metrics
from ml.evaluation.model_comparator import compare_models

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "ml" / "reports"


@pytest.fixture(scope="module")
def benchmark_results():
    """Load or run evaluation benchmark predictions on the held-out test split."""
    pred_path = REPORTS_DIR / "raw_test_predictions.json"
    if not pred_path.exists():
        runner = BenchmarkRunner()
        res = runner.run_benchmark()
        return res["predictions"]

    with open(pred_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_system_meets_overall_accuracy_target(benchmark_results):
    """TC-EVAL-01 & NFR-01: Verify overall system accuracy achieves >= 92.0%."""
    y_true = np.array([p["ground_truth"] for p in benchmark_results])
    y_pred = np.array([p["predicted_label"] for p in benchmark_results])
    y_prob = np.array([p["multimodal_prob"] for p in benchmark_results])

    metrics = calculate_metrics(y_true, y_pred, y_prob)
    acc = metrics["accuracy"]

    assert acc >= 0.92, f"Expected accuracy >= 0.92, got {acc:.4f}"


def test_system_meets_overall_f1_target(benchmark_results):
    """TC-EVAL-02 & NFR-01: Verify overall system F1-score achieves >= 0.92."""
    y_true = np.array([p["ground_truth"] for p in benchmark_results])
    y_pred = np.array([p["predicted_label"] for p in benchmark_results])
    y_prob = np.array([p["multimodal_prob"] for p in benchmark_results])

    metrics = calculate_metrics(y_true, y_pred, y_prob)
    f1 = metrics["f1_score"]

    assert f1 >= 0.92, f"Expected F1-score >= 0.92, got {f1:.4f}"


def test_system_roc_auc_exceeds_threshold(benchmark_results):
    """Verify system ROC-AUC achieves >= 0.95 on held-out test data."""
    y_true = np.array([p["ground_truth"] for p in benchmark_results])
    y_pred = np.array([p["predicted_label"] for p in benchmark_results])
    y_prob = np.array([p["multimodal_prob"] for p in benchmark_results])

    metrics = calculate_metrics(y_true, y_pred, y_prob)
    auc = metrics["roc_auc"]

    assert auc >= 0.95, f"Expected ROC-AUC >= 0.95, got {auc:.4f}"


def test_model_comparison_proves_multimodal_superiority(benchmark_results):
    """FR-TST-05: Proves multimodal score fusion outperforms single-branch architectures."""
    comparison = compare_models(benchmark_results)

    base_f1 = comparison["models"]["baseline_tabular_ml"]["f1_score"]
    vis_f1 = comparison["models"]["visual_cnn"]["f1_score"]
    multi_f1 = comparison["models"]["multimodal_fusion"]["f1_score"]

    assert multi_f1 >= base_f1, f"Multimodal F1 ({multi_f1}) should be >= Baseline F1 ({base_f1})"
    assert multi_f1 >= vis_f1, f"Multimodal F1 ({multi_f1}) should be >= Visual CNN F1 ({vis_f1})"
    assert comparison["deltas"]["f1_improvement_over_baseline_pct"] >= 0.0


def test_all_forgery_categories_detected(benchmark_results):
    """FR-TST-04: Asserts high sensitivity across all 5 distinct certificate
    manipulation modalities."""
    cat_breakdown = evaluate_categories(benchmark_results)

    for cat_name in FORGERY_CATEGORIES:
        assert cat_name in cat_breakdown["categories"], f"Missing category {cat_name}"
        detection_rate = cat_breakdown["categories"][cat_name]["detection_rate"]
        assert detection_rate >= 0.85, (
            f"Category '{cat_name}' detection rate {detection_rate:.2f} fell below 0.85"
        )

    assert cat_breakdown["overall_manipulation_detection_rate"] >= 0.90
