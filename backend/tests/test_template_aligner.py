import cv2
import numpy as np
import pytest

from app.modules.template_matching.aligner import align_to_template


def _create_sample_certificate_canvas(text: str = "UNIVERSITY OF CAMBRIDGE") -> np.ndarray:
    """Create a synthetic certificate image with rich text and border features for ORB detection."""
    img = np.ones((800, 1000, 3), dtype=np.uint8) * 255
    # Draw decorative outer borders
    cv2.rectangle(img, (20, 20), (980, 780), (30, 30, 30), 4)
    cv2.rectangle(img, (30, 30), (970, 770), (100, 100, 100), 2)
    # Add institutional emblem (circle with pattern)
    cv2.circle(img, (500, 150), 60, (0, 0, 180), -1)
    cv2.circle(img, (500, 150), 50, (255, 255, 255), 3)
    cv2.putText(img, "SEAL", (470, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Add distinct text blocks
    cv2.putText(img, text, (220, 260), cv2.FONT_HERSHEY_TRIPLEX, 1.1, (20, 20, 20), 2)
    cv2.putText(
        img, "THIS IS TO CERTIFY THAT", (320, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 2
    )
    cv2.putText(
        img, "ALICE ELIZABETH DOE", (280, 380), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 120), 2
    )
    cv2.putText(
        img,
        "HAS COMPLETED THE DEGREE OF",
        (310, 440),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (50, 50, 50),
        2,
    )
    cv2.putText(
        img, "BACHELOR OF SCIENCE", (290, 500), cv2.FONT_HERSHEY_TRIPLEX, 1.1, (20, 20, 20), 2
    )
    cv2.putText(
        img, "IN COMPUTER ENGINEERING", (300, 550), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (40, 40, 40), 2
    )
    cv2.putText(
        img, "FIRST CLASS WITH HONOURS", (310, 600), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 0), 2
    )
    cv2.putText(
        img, "ISSUED ON 2024-06-15", (380, 680), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (60, 60, 60), 1
    )

    return img


def test_align_to_template_identical_images():
    """Verify alignment of identical images yields 100% inliers and success."""
    template = _create_sample_certificate_canvas()
    query = template.copy()

    aligned, inlier_ratio, success = align_to_template(query, template)

    assert success is True
    assert inlier_ratio >= 0.70
    assert aligned.shape == template.shape


def test_align_to_template_with_slight_transformation():
    """Verify alignment recovers from small translation and scaling."""
    template = _create_sample_certificate_canvas()

    # Apply small affine transformation (translate 10px, scale 1.02)
    h, w = template.shape[:2]
    M = np.float32([[1.01, 0, 15], [0, 1.01, 10]])
    query = cv2.warpAffine(template, M, (w, h), borderValue=(255, 255, 255))

    aligned, inlier_ratio, success = align_to_template(query, template)

    assert success is True
    assert inlier_ratio >= 0.40
    assert aligned.shape == template.shape


def test_align_to_template_completely_different_image_fails():
    """Verify alignment fails gracefully when query is a completely different image."""
    template = _create_sample_certificate_canvas()
    # Query is random noise or blank
    query = np.zeros((800, 1000, 3), dtype=np.uint8)
    cv2.circle(query, (200, 200), 50, (255, 255, 255), -1)

    aligned, inlier_ratio, success = align_to_template(query, template)

    assert success is False
    assert inlier_ratio < 0.20


def test_align_to_template_none_inputs_raises_value_error():
    """Verify None input raises ValueError."""
    template = _create_sample_certificate_canvas()
    with pytest.raises(ValueError):
        align_to_template(None, template)
