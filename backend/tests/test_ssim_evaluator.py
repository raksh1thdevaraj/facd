import cv2
import numpy as np

from app.modules.template_matching.ssim_evaluator import (
    compute_template_ssim,
    evaluate_ssim_category,
)


def _create_base_template() -> np.ndarray:
    """Generate a clean base certificate image."""
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (15, 15), (785, 585), (20, 20, 20), 4)
    cv2.rectangle(img, (25, 25), (775, 575), (80, 80, 80), 2)
    cv2.putText(
        img,
        "OFFICIAL UNIVERSITY CERTIFICATE",
        (150, 100),
        cv2.FONT_HERSHEY_TRIPLEX,
        0.9,
        (0, 0, 0),
        2,
    )
    cv2.putText(
        img,
        "Awarded To: STUDENT NAME HERE",
        (150, 250),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 0),
        2,
    )
    cv2.putText(
        img, "Degree of Master of Science", (180, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2
    )
    return img


def test_tc_tmp_01_genuine_template_yields_high_ssim():
    """TC-TMP-01: Valid template matching achieves SSIM >= 0.85."""
    template = _create_base_template()
    query = template.copy()

    # Add very minor noise / compression artifact to simulate realistic scanned genuine doc
    noise = np.random.normal(0, 2, template.shape).astype(np.int16)
    query = np.clip(query.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    score, diff_map = compute_template_ssim(query, template)

    assert score >= 0.85, f"Expected SSIM >= 0.85 for genuine certificate, got {score}"
    assert evaluate_ssim_category(score) == "GENUINE_LAYOUT"
    assert diff_map.shape == template.shape[:2]


def test_tc_tmp_02_counterfeit_template_yields_low_ssim():
    """TC-TMP-02: Counterfeit template matching yields SSIM < 0.60."""
    template = _create_base_template()

    # Counterfeit document: completely altered layout, borders, and dark/colored background
    counterfeit = np.ones((600, 800, 3), dtype=np.uint8) * 60
    cv2.rectangle(counterfeit, (60, 60), (740, 540), (220, 220, 220), 4)
    cv2.circle(counterfeit, (400, 300), 120, (30, 30, 150), -1)
    cv2.putText(
        counterfeit,
        "COMPLETELY DIFFERENT UNIVERSITY",
        (80, 150),
        cv2.FONT_HERSHEY_COMPLEX,
        1.0,
        (255, 255, 255),
        2,
    )

    score, _ = compute_template_ssim(counterfeit, template)

    assert score < 0.60, f"Expected SSIM < 0.60 for counterfeit, got {score}"
    assert evaluate_ssim_category(score) == "COUNTERFEIT_LAYOUT"


def test_ssim_with_variable_mask_ignores_text_changes():
    """Masking student particulars ensures student-specific text does not lower template score."""
    template = _create_base_template()
    query = template.copy()

    # Modify student name area on query
    # "Awarded To: STUDENT NAME HERE" is at y: 220-270, x: 150-600
    cv2.rectangle(query, (140, 220), (600, 270), (255, 255, 255), -1)
    cv2.putText(
        query, "Awarded To: JANE DOE", (150, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2
    )

    # Without mask, score is penalized by student name difference
    unmasked_score, _ = compute_template_ssim(query, template)

    # With mask over the student name area
    var_mask = np.zeros(template.shape[:2], dtype=np.uint8)
    var_mask[210:280, 130:620] = 1

    masked_score, _ = compute_template_ssim(query, template, variable_mask=var_mask)

    # Masked score should be higher and >= 0.95 because non-masked layout is identical
    assert masked_score >= 0.95
    assert masked_score >= unmasked_score
