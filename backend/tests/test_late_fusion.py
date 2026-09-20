"""Unit tests for Weighted Late Fusion calculations and factor breakdowns."""

import pytest

from app.modules.score_fusion.late_fusion import WeightedLateFusion


def test_late_fusion_calculation_authentic():
    """Verify high authenticity input produces high authenticity score and low risk."""
    blender = WeightedLateFusion()
    auth_score, risk_score, sub_scores, factors = blender.blend(
        visual_fake_prob=0.05,
        tabular_fake_prob=0.05,
        forensic_score=0.95,
        text_consistency_score=0.90,
        template_score=0.92,
    )

    assert 0.85 <= auth_score <= 1.0
    assert 0.0 <= risk_score <= 15.0
    assert sub_scores.visual_branch_score == 0.95
    assert sub_scores.tabular_branch_score == 0.95
    assert len(factors) == 5
    assert all(f.impact == "LOW" for f in factors)


def test_late_fusion_calculation_manipulated():
    """Verify high fake probability produces low authenticity and high risk."""
    blender = WeightedLateFusion()
    auth_score, risk_score, sub_scores, factors = blender.blend(
        visual_fake_prob=0.85,
        tabular_fake_prob=0.90,
        forensic_score=0.20,
        text_consistency_score=0.30,
        template_score=0.40,
    )

    assert auth_score < 0.40
    assert risk_score > 60.0
    assert any(f.impact == "HIGH" for f in factors)


def test_late_fusion_custom_weights():
    """Verify custom weights normalization and score calculation."""
    custom_w = {"visual": 0.5, "tabular": 0.5, "forensic": 0.0, "text": 0.0, "template": 0.0}
    blender = WeightedLateFusion(weights=custom_w)

    auth_score, _, _, _ = blender.blend(
        visual_fake_prob=0.2,
        tabular_fake_prob=0.4,
        forensic_score=0.0,
        text_consistency_score=0.0,
        template_score=0.0,
    )

    # Expected: 0.5 * 0.8 + 0.5 * 0.6 = 0.70
    assert abs(auth_score - 0.70) < 1e-3


def test_late_fusion_invalid_weights():
    """Verify error on non-positive weights."""
    with pytest.raises(ValueError):
        WeightedLateFusion(weights={"visual": 0.0, "tabular": 0.0})
