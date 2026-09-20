"""Unit and integration tests for ScoreFusionService."""

import time
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.report import VerificationReportModel
from app.modules.score_fusion.service import ScoreFusionService
from app.schemas.decision import FinalVerificationDecision, VerificationVerdict
from app.schemas.pipeline import ScoreFusionOutput
from app.schemas.primitives import RiskBand
from app.schemas.template_matching import TierStatus


def test_score_fusion_service_end_to_end():
    """Verify service calculates final decision with all expected fields."""
    service = ScoreFusionService(default_fusion_method="late_fusion")
    decision = service.fuse_and_decide(
        certificate_id="cert-fusion-001",
        visual_fake_prob=0.10,
        tabular_fake_prob=0.12,
        forensic_score=0.92,
        text_consistency_score=0.94,
        template_score=0.88,
        tier_status=TierStatus.TIER_2_CONSISTENT,
    )

    assert isinstance(decision, FinalVerificationDecision)
    assert decision.certificate_id == "cert-fusion-001"
    assert decision.verdict == VerificationVerdict.AUTHENTIC
    assert decision.risk_band == RiskBand.LOW
    assert decision.overall_authenticity_score >= 0.85
    assert len(decision.contributing_factors) == 5
    assert decision.latency_ms > 0.0

    # Test SPEC-02 output conversion
    pipeline_out = decision.to_score_fusion_output()
    assert isinstance(pipeline_out, ScoreFusionOutput)
    assert pipeline_out.document_id == "cert-fusion-001"
    assert pipeline_out.risk_band == RiskBand.LOW


def test_score_fusion_service_latency():
    """Verify execution latency is strictly under 50ms (NFR-03 requirement < 100ms)."""
    service = ScoreFusionService()

    # Warmup
    _ = service.fuse_and_decide(
        certificate_id="warmup",
        visual_fake_prob=0.5,
        tabular_fake_prob=0.5,
        forensic_score=0.5,
        text_consistency_score=0.5,
        template_score=0.5,
    )

    t0 = time.perf_counter()
    _ = service.fuse_and_decide(
        certificate_id="bench",
        visual_fake_prob=0.3,
        tabular_fake_prob=0.2,
        forensic_score=0.8,
        text_consistency_score=0.85,
        template_score=0.9,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 50.0, f"Latency {elapsed_ms:.2f}ms exceeded 50ms target"


def test_score_fusion_service_db_persistence(tmp_path: Path):
    """Verify decision persistence to verification_reports database table."""
    engine = create_engine(f"sqlite:///{tmp_path}/reports_test.db")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    service = ScoreFusionService()
    decision = service.fuse_and_decide(
        certificate_id="cert-db-101",
        visual_fake_prob=0.85,
        tabular_fake_prob=0.90,
        forensic_score=0.20,
        text_consistency_score=0.25,
        template_score=0.30,
        db_session=session,
    )

    saved_report = (
        session.query(VerificationReportModel).filter_by(certificate_id="cert-db-101").first()
    )
    assert saved_report is not None
    assert saved_report.verdict == decision.verdict.value
    assert saved_report.overall_score == decision.overall_authenticity_score
    session.close()


def test_score_fusion_service_with_tier3_veto():
    """Verify Tier 3 record discrepancy forces MANIPULATED verdict via service."""
    service = ScoreFusionService()
    decision = service.fuse_and_decide(
        certificate_id="cert-veto-test",
        visual_fake_prob=0.05,  # Models think it's genuine
        tabular_fake_prob=0.05,
        forensic_score=0.95,
        text_consistency_score=0.95,
        template_score=0.90,
        tier_status=TierStatus.TIER_3_INCONSISTENT,
        record_found=True,
        discrepancies=["Name on certificate does not match database record"],
    )

    assert decision.veto_applied is True
    assert decision.verdict == VerificationVerdict.MANIPULATED
    assert decision.overall_authenticity_score <= 0.15
