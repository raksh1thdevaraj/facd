"""Unit tests for Natural Language Generation (NLG) engine."""

from types import SimpleNamespace

from app.modules.explainability.nlg_generator import NLGExplanationGenerator
from app.schemas.decision import (
    FinalVerificationDecision,
    SubScoresBreakdown,
    VerificationVerdict,
)
from app.schemas.explainability import FindingSeverity
from app.schemas.primitives import RiskBand


def _create_mock_decision(verdict: VerificationVerdict, score: float) -> FinalVerificationDecision:
    sub = SubScoresBreakdown(
        visual_branch_score=score,
        tabular_branch_score=score,
        text_consistency_score=score,
        forensic_score=score,
        template_score=score,
    )
    return FinalVerificationDecision(
        certificate_id="test-doc-123",
        overall_authenticity_score=score,
        overall_risk_score=(1.0 - score) * 100.0,
        risk_band=RiskBand.LOW if score >= 0.85 else RiskBand.HIGH,
        verdict=verdict,
        confidence=0.90,
        sub_scores=sub,
        tier_status="TIER_1_VERIFIED" if score >= 0.85 else "TIER_3_INCONSISTENT",
    )


def test_nlg_summary_paragraph_verdicts():
    """Verify generated executive summary reflects verdict (TC-EXP-04)."""
    dec_auth = _create_mock_decision(VerificationVerdict.AUTHENTIC, 0.95)
    p_auth = NLGExplanationGenerator.generate_summary_paragraph(dec_auth)
    assert "AUTHENTIC" in p_auth
    assert "high physical and typographical integrity" in p_auth

    dec_manip = _create_mock_decision(VerificationVerdict.MANIPULATED, 0.20)
    p_manip = NLGExplanationGenerator.generate_summary_paragraph(dec_manip)
    assert "MANIPULATED" in p_manip
    assert "digital tampering" in p_manip


def test_nlg_findings_bullets_synthesis():
    """Verify finding bullets synthesis across forensic and database signals."""
    decision = _create_mock_decision(VerificationVerdict.MANIPULATED, 0.30)

    # Mock forensic results
    copy_move_mock = SimpleNamespace(cloned_regions_count=2)
    ela_mock = SimpleNamespace(ela_score=0.45)
    forensic_mock = SimpleNamespace(copy_move=copy_move_mock, ela=ela_mock)

    # Mock record results
    record_mock = SimpleNamespace(
        record_found=True,
        discrepancies=["Student name on certificate 'Bob' does not match database 'Alice'"],
    )

    bullets = NLGExplanationGenerator.generate_finding_bullets(
        decision=decision,
        forensic_result=forensic_mock,
        record_result=record_mock,
    )

    assert len(bullets) >= 3
    # Check severity
    severities = [b.severity for b in bullets]
    assert FindingSeverity.CRITICAL in severities

    # Check database finding
    titles = [b.title for b in bullets]
    assert "Database Record Discrepancy" in titles
    assert "Copy-Move Splicing Detected" in titles
    assert "Compression Inconsistency (ELA)" in titles
