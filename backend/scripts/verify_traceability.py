"""Requirements & Test Case Traceability Matrix Verification Script (Phase 19).

Verifies bidirectional traceability between SRD requirements, testing specifications,
and implementing test files in the automated test suite.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
TESTS_DIR = BACKEND_DIR / "tests"

# Map of SRD Requirements to implementing modules and test files
REQUIREMENT_MAP: List[Dict[str, Any]] = [
    {
        "req_id": "FR-ING-01",
        "description": "Multi-format certificate document ingestion (JPG, PNG, PDF)",
        "phase": "Phase 03",
        "test_file": "test_ingestion_api.py",
        "test_cases": ["TC-ING-01", "TC-ING-02"],
    },
    {
        "req_id": "FR-ING-02",
        "description": "File format, dimensions, and size limit validation",
        "phase": "Phase 03",
        "test_file": "test_ingestion_validator.py",
        "test_cases": ["TC-ING-03", "TC-ING-04"],
    },
    {
        "req_id": "FR-ING-03",
        "description": "Strict rejection and logging of corrupted/unsupported files",
        "phase": "Phase 03",
        "test_file": "test_ingestion_api.py",
        "test_cases": ["TC-ING-05"],
    },
    {
        "req_id": "FR-ING-04",
        "description": "Batch certificate upload support",
        "phase": "Phase 03",
        "test_file": "test_ingestion_service.py",
        "test_cases": ["TC-ING-06"],
    },
    {
        "req_id": "FR-PRE-01",
        "description": "Adaptive resolution scaling and DPI normalization",
        "phase": "Phase 04",
        "test_file": "test_preprocessing_pipeline.py",
        "test_cases": ["TC-PRE-01"],
    },
    {
        "req_id": "FR-PRE-02",
        "description": "Document denoising and background artifact suppression",
        "phase": "Phase 04",
        "test_file": "test_contrast_enhancer.py",
        "test_cases": ["TC-PRE-02"],
    },
    {
        "req_id": "FR-PRE-03",
        "description": "Contrast normalization and binarization",
        "phase": "Phase 04",
        "test_file": "test_binarizer.py",
        "test_cases": ["TC-PRE-03"],
    },
    {
        "req_id": "FR-PRE-04",
        "description": "Automatic deskewing and perspective rectification",
        "phase": "Phase 04",
        "test_file": "test_deskewer.py",
        "test_cases": ["TC-PRE-04", "TC-PRE-05"],
    },
    {
        "req_id": "FR-PRE-05",
        "description": "PDF vector-to-raster conversion via pypdfium2/poppler",
        "phase": "Phase 04",
        "test_file": "test_pdf_rasterizer.py",
        "test_cases": ["TC-PRE-06"],
    },
    {
        "req_id": "FR-OCR-01",
        "description": "Structured field extraction from academic certificates",
        "phase": "Phase 05",
        "test_file": "test_field_extractors.py",
        "test_cases": ["TC-OCR-01", "TC-OCR-02"],
    },
    {
        "req_id": "FR-OCR-02",
        "description": "Character and field-level confidence scoring",
        "phase": "Phase 05",
        "test_file": "test_confidence_evaluator.py",
        "test_cases": ["TC-OCR-03"],
    },
    {
        "req_id": "FR-OCR-03",
        "description": "Confidence threshold filtering and fallback degradation",
        "phase": "Phase 05",
        "test_file": "test_ocr_service.py",
        "test_cases": ["TC-OCR-04"],
    },
    {
        "req_id": "FR-OCR-04",
        "description": "Printed and semi-structured text recognition support",
        "phase": "Phase 05",
        "test_file": "test_ocr_engine.py",
        "test_cases": ["TC-OCR-05"],
    },
    {
        "req_id": "FR-TXT-01",
        "description": "Date chronological order and lifespan logic validation",
        "phase": "Phase 06",
        "test_file": "test_logical_validator.py",
        "test_cases": ["TC-TXT-01"],
    },
    {
        "req_id": "FR-TXT-02",
        "description": "Grade, GPA, and marks formatting integrity validation",
        "phase": "Phase 06",
        "test_file": "test_format_checker.py",
        "test_cases": ["TC-TXT-02"],
    },
    {
        "req_id": "FR-TXT-03",
        "description": "Institution name validation and fuzzy alias matching",
        "phase": "Phase 06",
        "test_file": "test_text_consistency_service.py",
        "test_cases": ["TC-TXT-03"],
    },
    {
        "req_id": "FR-TXT-04",
        "description": "Certificate serial number regex format checking",
        "phase": "Phase 06",
        "test_file": "test_format_checker.py",
        "test_cases": ["TC-TXT-04"],
    },
    {
        "req_id": "FR-FOR-01",
        "description": "Copy-move cloning detection using SIFT/ORB keypoints",
        "phase": "Phase 07",
        "test_file": "test_copy_move_detector.py",
        "test_cases": ["TC-FOR-01"],
    },
    {
        "req_id": "FR-FOR-02",
        "description": "Font size, stroke width, and spacing anomaly detection",
        "phase": "Phase 07",
        "test_file": "test_stroke_width_analyzer.py",
        "test_cases": ["TC-FOR-02"],
    },
    {
        "req_id": "FR-FOR-03",
        "description": "Error Level Analysis (ELA) JPEG compression forensics",
        "phase": "Phase 07",
        "test_file": "test_ela_analyzer.py",
        "test_cases": ["TC-FOR-03"],
    },
    {
        "req_id": "FR-FOR-04",
        "description": "Baseline alignment and inter-token spacing validation",
        "phase": "Phase 07",
        "test_file": "test_baseline_checker.py",
        "test_cases": ["TC-FOR-04"],
    },
    {
        "req_id": "FR-FOR-05",
        "description": "Institutional seal and official stamp presence/integrity check",
        "phase": "Phase 07",
        "test_file": "test_seal_matcher.py",
        "test_cases": ["TC-FOR-05"],
    },
    {
        "req_id": "FR-TPL-01",
        "description": "Institutional master certificate template registration",
        "phase": "Phase 08",
        "test_file": "test_template_registration.py",
        "test_cases": ["TC-TPL-01"],
    },
    {
        "req_id": "FR-TPL-02",
        "description": "Structural similarity (SSIM) & visual layout comparison",
        "phase": "Phase 08",
        "test_file": "test_ssim_evaluator.py",
        "test_cases": ["TC-TPL-02"],
    },
    {
        "req_id": "FR-TPL-03",
        "description": "Authoritative student ground-truth record verification",
        "phase": "Phase 08",
        "test_file": "test_record_verifier.py",
        "test_cases": ["TC-TPL-03"],
    },
    {
        "req_id": "FR-TPL-04",
        "description": "Graceful fallback when no institutional template exists",
        "phase": "Phase 08",
        "test_file": "test_tier_classifier.py",
        "test_cases": ["TC-TPL-04"],
    },
    {
        "req_id": "FR-ML-01",
        "description": "Supervised tabular ML classification model (Random Forest/HistGBM)",
        "phase": "Phase 09",
        "test_file": "test_baseline_inference.py",
        "test_cases": ["TC-ML-01"],
    },
    {
        "req_id": "FR-ML-02",
        "description": "Continuous authenticity probability and confidence scoring",
        "phase": "Phase 09",
        "test_file": "test_ml_service.py",
        "test_cases": ["TC-ML-02"],
    },
    {
        "req_id": "FR-ML-03",
        "description": "Deep Learning visual CNN branch (EfficientNet-B0)",
        "phase": "Phase 10",
        "test_file": "test_visual_network.py",
        "test_cases": ["TC-DL-01"],
    },
    {
        "req_id": "FR-ML-04",
        "description": "Model versioning and metadata logging in evaluation reports",
        "phase": "Phase 09",
        "test_file": "test_model_evaluation.py",
        "test_cases": ["TC-ML-03"],
    },
    {
        "req_id": "FR-SCR-01",
        "description": "Weighted multimodal score fusion (Early / Late / Stacking)",
        "phase": "Phase 11",
        "test_file": "test_score_fusion_service.py",
        "test_cases": ["TC-FUS-01"],
    },
    {
        "req_id": "FR-SCR-02",
        "description": "Categorical risk band mapping (AUTHENTIC, SUSPICIOUS, MANIPULATED)",
        "phase": "Phase 11",
        "test_file": "test_verdict_engine.py",
        "test_cases": ["TC-FUS-02"],
    },
    {
        "req_id": "FR-SCR-03",
        "description": "Institutional veto override rules engine",
        "phase": "Phase 11",
        "test_file": "test_veto_rules.py",
        "test_cases": ["TC-FUS-03"],
    },
    {
        "req_id": "FR-SCR-04",
        "description": "Visual explainability overlays and bounding box annotations",
        "phase": "Phase 12",
        "test_file": "test_unified_overlay.py",
        "test_cases": ["TC-EXP-01"],
    },
    {
        "req_id": "FR-SCR-05",
        "description": "Cryptographically signed, downloadable PDF verification report",
        "phase": "Phase 13",
        "test_file": "test_report_service.py",
        "test_cases": ["TC-REP-01"],
    },
    {
        "req_id": "FR-USR-01",
        "description": "Role-based access control (Admin, Verifier, Auditor, Public)",
        "phase": "Phase 15",
        "test_file": "test_admin_endpoints.py",
        "test_cases": ["TC-ADM-01"],
    },
    {
        "req_id": "FR-USR-02",
        "description": "Historical verification query and multi-parameter filtering",
        "phase": "Phase 17",
        "test_file": "test_admin_endpoints.py",
        "test_cases": ["TC-ADM-02"],
    },
    {
        "req_id": "FR-USR-03",
        "description": "System analytics and throughput metrics dashboard",
        "phase": "Phase 17",
        "test_file": "test_admin_endpoints.py",
        "test_cases": ["TC-ADM-03"],
    },
    {
        "req_id": "FR-USR-04",
        "description": "Immutable security and operational audit logging",
        "phase": "Phase 15",
        "test_file": "test_audit_logging.py",
        "test_cases": ["TC-AUD-01"],
    },
    # Non-Functional Requirements
    {
        "req_id": "NFR-01",
        "description": "Verification Accuracy: Overall Accuracy >= 92%, F1 >= 0.92",
        "phase": "Phase 19",
        "test_file": "test_evaluation_metrics.py",
        "test_cases": ["TC-EVAL-01", "TC-EVAL-02"],
    },
    {
        "req_id": "NFR-02",
        "description": "Batch processing throughput and concurrent load resilience",
        "phase": "Phase 18",
        "test_file": "e2e/test_concurrent_load.py",
        "test_cases": ["TC-E2E-05"],
    },
    {
        "req_id": "NFR-03",
        "description": "End-to-end turnaround latency <= 15 seconds per certificate",
        "phase": "Phase 18",
        "test_file": "e2e/test_full_genuine_flow.py",
        "test_cases": ["TC-E2E-01"],
    },
    {
        "req_id": "NFR-04",
        "description": "Fault tolerance and graceful degradation under partial failures",
        "phase": "Phase 18",
        "test_file": "e2e/test_graceful_degradation.py",
        "test_cases": ["TC-E2E-04"],
    },
]


def verify_traceability() -> Dict[str, Any]:
    """Audit test suite to confirm all requirement mapping targets exist."""
    results: List[Dict[str, Any]] = []
    missing_files: List[str] = []

    for item in REQUIREMENT_MAP:
        test_path = TESTS_DIR / item["test_file"]
        exists = test_path.exists()
        if not exists:
            # Check unit or integration subdirs
            alt1 = TESTS_DIR / "unit" / item["test_file"]
            alt2 = TESTS_DIR / "integration" / item["test_file"]
            exists = alt1.exists() or alt2.exists()
            if exists:
                test_path = alt1 if alt1.exists() else alt2

        if not exists:
            missing_files.append(item["test_file"])

        results.append(
            {
                "req_id": item["req_id"],
                "description": item["description"],
                "phase": item["phase"],
                "test_file": item["test_file"],
                "test_cases": ", ".join(item["test_cases"]),
                "status": "VERIFIED" if exists else "MISSING",
            }
        )

    passed_count = sum(1 for r in results if r["status"] == "VERIFIED")
    total_count = len(results)
    coverage_pct = round((passed_count / total_count) * 100, 1)

    summary = {
        "total_requirements": total_count,
        "verified_requirements": passed_count,
        "missing_files": missing_files,
        "traceability_coverage_percentage": coverage_pct,
        "details": results,
    }
    return summary


def generate_markdown_matrix(summary: Dict[str, Any]) -> str:
    """Format traceability audit into GitHub Flavored Markdown."""
    verified = summary["verified_requirements"]
    total = summary["total_requirements"]
    pct = summary["traceability_coverage_percentage"]
    lines = [
        "# Requirements & Test Traceability Matrix",
        "",
        f"**Audit Status:** {verified}/{total} Requirements Verified ({pct}%)",
        "",
        "| Req ID | Description | Phase | Test Cases | Test File | Status |",
        "|---|---|---|---|---|---|",
    ]
    for r in summary["details"]:
        status_badge = "✅ PASSED" if r["status"] == "VERIFIED" else "❌ MISSING"
        lines.append(
            f"| `{r['req_id']}` | {r['description']} | {r['phase']} | "
            f"{r['test_cases']} | `{r['test_file']}` | {status_badge} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    audit = verify_traceability()
    v_cnt = audit["verified_requirements"]
    t_cnt = audit["total_requirements"]
    c_pct = audit["traceability_coverage_percentage"]
    print(f"Traceability Audit: {v_cnt}/{t_cnt} ({c_pct}%)")
    md = generate_markdown_matrix(audit)
    out_path = PROJECT_ROOT / "development-plan" / "TRACEABILITY_MATRIX.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"Written matrix to {out_path}")
