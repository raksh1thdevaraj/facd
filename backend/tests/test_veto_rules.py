"""Unit tests for Institutional Veto Override Engine."""

from app.modules.score_fusion.veto_rules import InstitutionalVetoEngine
from app.schemas.template_matching import TierStatus


def test_veto_tier_1_verified_boosts_score():
    """Verify Tier 1 exact record match overrides lower ML score to >= 0.95 (TC-FUS-05)."""
    raw_score = 0.68  # Borderline statistical score
    adjusted, veto_applied, reason = InstitutionalVetoEngine.apply_vetoes(
        raw_authenticity_score=raw_score,
        tier_status=TierStatus.TIER_1_VERIFIED,
        record_found=True,
    )

    assert veto_applied is True
    assert adjusted >= 0.95
    assert "CONFIRMATION VETO" in (reason or "")


def test_veto_tier_3_inconsistent_record_mismatch():
    """Verify Tier 3 record discrepancy forces high ML score down to <= 0.15 (TC-FUS-05)."""
    raw_score = 0.98  # Very high statistical score
    adjusted, veto_applied, reason = InstitutionalVetoEngine.apply_vetoes(
        raw_authenticity_score=raw_score,
        tier_status=TierStatus.TIER_3_INCONSISTENT,
        record_found=True,
        discrepancies=["Student name on certificate 'Bob' does not match database 'Alice'"],
    )

    assert veto_applied is True
    assert adjusted <= 0.15
    assert "CRITICAL VETO" in (reason or "")
    assert "Student name" in (reason or "")


def test_veto_tier_3_counterfeit_template():
    """Verify Tier 3 counterfeit template forces score down to <= 0.25."""
    raw_score = 0.90
    adjusted, veto_applied, reason = InstitutionalVetoEngine.apply_vetoes(
        raw_authenticity_score=raw_score,
        tier_status=TierStatus.TIER_3_INCONSISTENT,
        primary_reason="Counterfeit or mismatched template",
    )

    assert veto_applied is True
    assert adjusted <= 0.25
    assert "visual structure contradicts" in (reason or "")


def test_no_veto_tier_2_consistent():
    """Verify Tier 2 consistent template does not trigger veto override."""
    raw_score = 0.82
    adjusted, veto_applied, reason = InstitutionalVetoEngine.apply_vetoes(
        raw_authenticity_score=raw_score,
        tier_status=TierStatus.TIER_2_CONSISTENT,
    )

    assert veto_applied is False
    assert adjusted == 0.82
    assert reason is None
