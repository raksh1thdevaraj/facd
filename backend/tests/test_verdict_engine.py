"""Unit tests for VerdictEngine score mapping and confidence calibration."""

from app.modules.score_fusion.verdict_engine import VerdictEngine
from app.schemas.decision import VerificationVerdict
from app.schemas.primitives import RiskBand


def test_verdict_authentic_boundary():
    """Verify score >= 0.85 maps to AUTHENTIC and LOW risk (TC-FUS-04)."""
    verdict, risk_band, confidence, rationale = VerdictEngine.evaluate(0.92)
    assert verdict == VerificationVerdict.AUTHENTIC
    assert risk_band == RiskBand.LOW
    assert 0.70 <= confidence <= 1.0
    assert "high integrity" in rationale.lower()


def test_verdict_suspicious_boundary():
    """Verify score 0.60 <= s < 0.85 maps to SUSPICIOUS and MEDIUM risk (TC-FUS-04)."""
    verdict, risk_band, confidence, rationale = VerdictEngine.evaluate(0.72)
    assert verdict == VerificationVerdict.SUSPICIOUS
    assert risk_band == RiskBand.MEDIUM
    assert 0.50 <= confidence <= 0.70
    assert "inconclusive" in rationale.lower() or "borderline" in rationale.lower()


def test_verdict_manipulated_boundary():
    """Verify score < 0.60 maps to MANIPULATED and HIGH risk (TC-FUS-04)."""
    verdict, risk_band, confidence, rationale = VerdictEngine.evaluate(0.35)
    assert verdict == VerificationVerdict.MANIPULATED
    assert risk_band == RiskBand.HIGH
    assert 0.70 <= confidence <= 1.0
    assert "fake" in rationale.lower()


def test_verdict_veto_rationale():
    """Verify veto reasons are reflected in verdict summary rationale."""
    verdict, _, _, rationale = VerdictEngine.evaluate(
        0.10,
        veto_applied=True,
        veto_reason="CRITICAL VETO: Roll number mismatch",
    )
    assert verdict == VerificationVerdict.MANIPULATED
    assert "Roll number mismatch" in rationale
