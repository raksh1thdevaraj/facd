"""Unit and integration tests for ExplainabilityService."""

import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image

from app.modules.explainability.service import ExplainabilityService
from app.schemas.decision import (
    FinalVerificationDecision,
    SubScoresBreakdown,
    VerificationVerdict,
)
from app.schemas.explainability import ExplainabilityReport
from app.schemas.primitives import BoundingBox, RiskBand


def test_explainability_service_end_to_end(tmp_path: Path):
    """Verify end-to-end explainability report and interactive JSON generation."""
    raw_img = tmp_path / "cert_explain.png"
    Image.new("RGB", (1200, 1600), color=(250, 250, 245)).save(raw_img)

    sub = SubScoresBreakdown(
        visual_branch_score=0.25,
        tabular_branch_score=0.30,
        text_consistency_score=0.40,
        forensic_score=0.35,
        template_score=0.50,
    )
    decision = FinalVerificationDecision(
        certificate_id="cert-exp-001",
        overall_authenticity_score=0.32,
        overall_risk_score=68.0,
        risk_band=RiskBand.HIGH,
        verdict=VerificationVerdict.MANIPULATED,
        confidence=0.85,
        sub_scores=sub,
        tier_status="TIER_3_UNVERIFIED",
    )

    # Mock text anomaly with normalized bbox
    anom_mock = SimpleNamespace(
        type="Baseline Drift",
        description="Text line tilted 3px",
        bbox=BoundingBox(x1=0.2, y1=0.3, x2=0.5, y2=0.35),
    )
    text_mock = SimpleNamespace(anomalies=[anom_mock])

    # Mock copy move region
    region_mock = SimpleNamespace(bbox=SimpleNamespace(x=100, y=200, width=80, height=80))
    copy_move_mock = SimpleNamespace(cloned_regions_count=1, regions=[region_mock])
    forensic_mock = SimpleNamespace(copy_move=copy_move_mock)

    tabular_feats = np.random.randn(22).astype(np.float32)

    service = ExplainabilityService()
    report = service.explain_certificate(
        certificate_id="cert-exp-001",
        raw_image_path=raw_img,
        decision=decision,
        tabular_features=tabular_feats,
        text_result=text_mock,
        forensic_result=forensic_mock,
        output_dir=tmp_path / "reports",
    )

    assert isinstance(report, ExplainabilityReport)
    assert report.certificate_id == "cert-exp-001"
    assert "MANIPULATED" in report.primary_verdict_rationale
    assert len(report.key_findings) > 0
    assert len(report.top_contributing_features) > 0
    assert len(report.spatial_anomalies) == 2  # 1 text + 1 clone

    # Check interactive overlay payload
    assert report.interactive_overlay.image_width == 1200
    assert report.interactive_overlay.image_height == 1600
    assert len(report.interactive_overlay.anomalies) == 2

    # Check overlay image exists
    assert report.unified_overlay_path is not None
    assert Path(report.unified_overlay_path).exists()


def test_explainability_latency_benchmark(tmp_path: Path):
    """Verify explainability pipeline latency is well below 2.0 seconds (NFR-03)."""
    raw_img = tmp_path / "cert_bench.png"
    Image.new("RGB", (800, 1000), color=(255, 255, 255)).save(raw_img)

    sub = SubScoresBreakdown(
        visual_branch_score=0.90,
        tabular_branch_score=0.90,
        text_consistency_score=0.90,
        forensic_score=0.90,
        template_score=0.90,
    )
    decision = FinalVerificationDecision(
        certificate_id="bench-cert",
        overall_authenticity_score=0.90,
        overall_risk_score=10.0,
        risk_band=RiskBand.LOW,
        verdict=VerificationVerdict.AUTHENTIC,
        confidence=0.90,
        sub_scores=sub,
    )
    tabular_feats = np.random.randn(22).astype(np.float32)

    service = ExplainabilityService()

    t0 = time.perf_counter()
    res = service.explain_certificate(
        certificate_id="bench-cert",
        raw_image_path=raw_img,
        decision=decision,
        tabular_features=tabular_feats,
        output_dir=tmp_path / "bench_reports",
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert elapsed_ms < 2000.0, f"Explainability latency {elapsed_ms:.2f}ms exceeded 2000ms"
    assert res.execution_time_ms > 0.0
