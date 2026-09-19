import time
from pathlib import Path

import numpy as np

from app.modules.ocr.token_builder import TokenBuilder
from app.modules.text_consistency.score_aggregator import ScoreAggregator
from app.modules.text_consistency.service import (
    TextConsistencyService,
    get_text_consistency_service,
)
from app.schemas.pipeline import CertificateFields, TextConsistencyOutput
from app.schemas.primitives import CheckStatus
from app.schemas.text_consistency import (
    AnomalousRegion,
    AnomalyType,
    TextConsistencyConfig,
    TextConsistencyResult,
)


def test_composite_score_calculation():
    """TC-TXT-04: Verify weighted composite scoring and critical veto penalty."""
    config = TextConsistencyConfig(
        weight_baseline=0.25,
        weight_font_size=0.20,
        weight_stroke_weight=0.20,
        weight_spacing=0.15,
        weight_logical=0.20,
    )
    aggregator = ScoreAggregator(config=config)

    # 1. Clean sub-scores -> composite score near 1.0
    score, checks = aggregator.aggregate(
        baseline_score=1.0,
        font_size_score=1.0,
        stroke_weight_score=1.0,
        spacing_score=1.0,
        format_score=1.0,
        logical_score=1.0,
        anomalies=[],
        existing_checks=[],
    )
    assert score == 1.0
    assert len(checks) == 5  # 5 checks generated

    # 2. Veto penalty: critical logic error caps score at 0.40
    critical_anomaly = AnomalousRegion(
        anomaly_type=AnomalyType.LOGICAL_CONTRADICTION,
        severity=1.0,
        description="Issue date in future",
        bbox=TokenBuilder.create_token("2035", 0.95, 10, 10, 50, 20, 100, 100).bbox,
    )
    score_veto, _ = aggregator.aggregate(
        baseline_score=1.0,
        font_size_score=1.0,
        stroke_weight_score=1.0,
        spacing_score=1.0,
        format_score=1.0,
        logical_score=0.20,
        anomalies=[critical_anomaly],
        existing_checks=[],
    )
    assert score_veto <= 0.40


def test_service_end_to_end_clean_certificate(tmp_path: Path):
    """Run full TextConsistencyService on clean certificate and verify high authenticity score."""
    service = TextConsistencyService(report_dir=tmp_path)

    # Clean certificate layout with 2 lines of text
    tokens_line1 = [
        TokenBuilder.create_token("STANFORD", 0.98, 100, 100, 120, 25, 1000, 1000),
        TokenBuilder.create_token("UNIVERSITY", 0.98, 230, 100, 140, 25, 1000, 1000),
        TokenBuilder.create_token("DEGREE", 0.98, 380, 100, 100, 25, 1000, 1000),
    ]
    tokens_line2 = [
        TokenBuilder.create_token("Bachelor", 0.98, 100, 160, 90, 20, 1000, 1000),
        TokenBuilder.create_token("of", 0.98, 200, 160, 25, 20, 1000, 1000),
        TokenBuilder.create_token("Science", 0.98, 235, 160, 80, 20, 1000, 1000),
        TokenBuilder.create_token("2022", 0.98, 325, 160, 50, 20, 1000, 1000),
    ]
    all_tokens = tokens_line1 + tokens_line2

    fields = CertificateFields(
        student_name="Jane Doe",
        register_number="SU2022001",
        course_degree="Bachelor of Science",
        grade_or_marks="First Class",
        issue_date="2022-06-20",
    )

    dummy_image = np.full((1000, 1000, 3), 255, dtype=np.uint8)

    result = service.analyze(
        document_id="doc_clean_001",
        ocr_tokens=all_tokens,
        image_or_path=dummy_image,
        extracted_fields=fields,
    )

    assert isinstance(result, TextConsistencyResult)
    assert result.overall_text_consistency_score >= 0.85
    assert result.status == CheckStatus.PASSED
    assert result.consistency_risk_score <= 15.0
    assert len(result.anomalous_regions) == 0
    assert result.visualization_image_path is not None
    assert Path(result.visualization_image_path).exists()


def test_service_end_to_end_forged_certificate(tmp_path: Path):
    """Run full TextConsistencyService on forged certificate containing multiple anomalies."""
    service = TextConsistencyService(report_dir=tmp_path)

    # Line with raised baseline (+8px) and oversized font (18px vs 12px)
    tokens = [
        TokenBuilder.create_token("Class", 0.95, 100, 100, 60, 12, 1000, 1000),
        TokenBuilder.create_token("is", 0.95, 170, 100, 25, 12, 1000, 1000),
        TokenBuilder.create_token(
            "DISTINCTION", 0.95, 205, 92, 120, 20, 1000, 1000
        ),  # Raised & Oversized
        TokenBuilder.create_token("Awarded", 0.95, 335, 100, 80, 12, 1000, 1000),
    ]

    # Future issue date 2038
    fields = CertificateFields(
        student_name="Malicious Actor",
        course_degree="Master of Science",
        grade_or_marks="105%",  # Out of bounds percentage
        issue_date="2038-01-01",  # Future date
    )

    dummy_image = np.full((1000, 1000, 3), 255, dtype=np.uint8)

    result = service.analyze(
        document_id="doc_forged_001",
        ocr_tokens=tokens,
        image_or_path=dummy_image,
        extracted_fields=fields,
    )

    assert result.overall_text_consistency_score <= 0.40
    assert result.status == CheckStatus.FAILED
    assert result.consistency_risk_score >= 60.0
    assert len(result.anomalous_regions) >= 2


def test_pipeline_output_contract_spec02():
    """Verify that analyze_to_pipeline_output produces valid SPEC-02 TextConsistencyOutput."""
    service = get_text_consistency_service()

    tokens = [
        TokenBuilder.create_token("Bachelor", 0.95, 100, 100, 80, 20, 1000, 1000),
        TokenBuilder.create_token("of", 0.95, 190, 100, 20, 20, 1000, 1000),
        TokenBuilder.create_token("Arts", 0.95, 220, 100, 50, 20, 1000, 1000),
    ]

    output = service.analyze_to_pipeline_output(
        document_id="spec02_test_doc",
        ocr_tokens=tokens,
    )

    assert isinstance(output, TextConsistencyOutput)
    assert output.document_id == "spec02_test_doc"
    assert output.overall_status in (CheckStatus.PASSED, CheckStatus.WARNING, CheckStatus.FAILED)
    assert 0.0 <= output.consistency_risk_score <= 100.0
    assert len(output.checks) >= 5


def test_performance_under_two_seconds():
    """NFR-03: Performance requirement (< 2.0s per certificate)."""
    service = get_text_consistency_service()

    # Generate 50 realistic tokens across 5 lines
    tokens = []
    for line_idx in range(5):
        y = 100 + line_idx * 50
        for token_idx in range(10):
            x = 50 + token_idx * 90
            tokens.append(
                TokenBuilder.create_token(
                    f"Word{line_idx}_{token_idx}",
                    0.95,
                    x,
                    y,
                    80,
                    20,
                    1000,
                    1000,
                )
            )

    start = time.perf_counter()
    result = service.analyze(
        document_id="perf_test_doc",
        ocr_tokens=tokens,
    )
    elapsed = time.perf_counter() - start

    assert elapsed < 2.0
    assert result.execution_time_ms < 2000.0
