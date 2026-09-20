import cv2
import numpy as np

from app.modules.template_matching.seal_matcher import match_seal_and_logo
from app.schemas.template_matching import SealROI


def _create_template_with_seal() -> np.ndarray:
    """Create a sample canvas with an emblem at (100, 100, 80, 80)."""
    canvas = np.ones((500, 500, 3), dtype=np.uint8) * 240
    # Draw gold/red emblem at (100, 100, 80, 80)
    cv2.circle(canvas, (140, 140), 35, (0, 140, 255), -1)  # Gold circle
    cv2.circle(canvas, (140, 140), 25, (0, 0, 180), -1)  # Inner red circle
    cv2.putText(canvas, "UNIV", (122, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    return canvas


def test_seal_verification_genuine_match():
    """Verify authentic seal yields high composite score >= 0.80."""
    template = _create_template_with_seal()
    query = template.copy()

    roi = SealROI(x=100, y=100, width=80, height=80)
    score, r_max, hist_corr = match_seal_and_logo(query, template, roi)

    assert score >= 0.85
    assert r_max >= 0.90
    assert hist_corr >= 0.85


def test_seal_verification_detects_altered_or_different_logo():
    """Verify altered or replaced seal yields score < 0.50."""
    template = _create_template_with_seal()
    query = template.copy()

    # Tamper with seal area in query image: replace with blue square
    cv2.rectangle(query, (100, 100), (180, 180), (200, 0, 0), -1)

    roi = {"x": 100, "y": 100, "width": 80, "height": 80}
    score, r_max, hist_corr = match_seal_and_logo(query, template, roi)

    assert score < 0.50, f"Expected altered seal score < 0.50, got {score}"


def test_seal_verification_invalid_roi_returns_zero():
    """Verify out-of-bounds or zero-size ROI returns 0.0 without crashing."""
    template = _create_template_with_seal()
    query = template.copy()

    invalid_roi = {"x": 600, "y": 600, "width": 50, "height": 50}
    score, r_max, hist_corr = match_seal_and_logo(query, template, invalid_roi)

    assert score == 0.0
    assert r_max == 0.0
