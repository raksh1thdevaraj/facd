"""Unit tests for coverage, ablation study, and report generation (Phase 19 - CHIP TST-12).

Verifies:
- TC-EVAL-03: Formal Evaluation Report and JSON generation
- TC-EVAL-04: Ablation study execution and subsystem impact quantification
- TC-EVAL-05: Code test coverage configuration and traceability compliance
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    from backend.scripts.verify_traceability import verify_traceability
except ModuleNotFoundError:
    from scripts.verify_traceability import verify_traceability

from ml.evaluation.ablation_runner import run_ablation_study
from ml.evaluation.report_writer import generate_evaluation_report

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "ml" / "reports"


@pytest.fixture(scope="module")
def benchmark_predictions():
    """Load cached benchmark predictions."""
    pred_path = REPORTS_DIR / "raw_test_predictions.json"
    with open(pred_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_ablation_study_quantifies_impact(benchmark_predictions):
    """TC-EVAL-04 & FR-TST-06: Verify feature ablation study proves multi-subsystem contribution."""
    ablation = run_ablation_study(benchmark_predictions)

    results = ablation["results"]
    assert len(results) >= 5, "Expected at least 5 ablation configurations"

    full_system = next((r for r in results if r["config_id"] == "full_system"), None)
    assert full_system is not None
    assert full_system["f1_score"] >= 0.92

    # Verify removing features degrades performance (delta F1 <= 0)
    for r in results:
        if r["config_id"] != "full_system":
            assert r["delta_f1_pct"] <= 0.0, (
                f"Module removal {r['disabled_module']} should degrade or maintain score"
            )


def test_evaluation_report_file_generation():
    """TC-EVAL-03: Verify formal evaluation report (Markdown + JSON)
    is generated with all sections."""
    rep_summary = generate_evaluation_report()

    md_path = Path(rep_summary["md_path"])
    json_path = Path(rep_summary["json_path"])

    assert md_path.exists(), f"Markdown report missing at {md_path}"
    assert json_path.exists(), f"JSON summary missing at {json_path}"

    content = md_path.read_text(encoding="utf-8")
    assert "Executive Summary" in content
    assert "Confusion Matrix" in content
    assert "Comparative Model Performance Benchmark" in content
    assert "Fine-Grained Forgery Modality Breakdown" in content
    assert "Subsystem Feature Ablation Study" in content
    assert "Latency and Throughput Profiling" in content
    assert "PASSED" in content

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["nfr_01_passed"] is True
        assert data["overall_metrics"]["accuracy"] >= 0.92
        assert data["overall_metrics"]["f1_score"] >= 0.92


def test_traceability_matrix_completeness():
    """Verify bidirectional traceability matrix achieves 100% requirement verification."""
    summary = verify_traceability()

    assert summary["missing_files"] == [], f"Missing test files: {summary['missing_files']}"
    assert summary["traceability_coverage_percentage"] == 100.0
    assert summary["verified_requirements"] == summary["total_requirements"]


def test_chart_artifacts_exist_and_non_empty():
    """Verify all 5 high-resolution evaluation chart artifacts exist and have valid size."""
    expected_charts = [
        "evaluation_confusion_matrix.png",
        "comparative_roc_curves.png",
        "precision_recall_curves.png",
        "category_breakdown.png",
        "ablation_study_chart.png",
    ]

    for chart_name in expected_charts:
        chart_file = REPORTS_DIR / chart_name
        assert chart_file.exists(), f"Chart artifact missing: {chart_name}"
        assert chart_file.stat().st_size > 5000, f"Chart artifact too small: {chart_name}"
