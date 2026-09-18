import cv2
import numpy as np

from app.modules.preprocessing.deskewer import (
    Deskewer,
    estimate_skew_angle,
    rotate_image,
)


def create_synthetic_text_image(angle_deg: float = 0.0) -> np.ndarray:
    """Create a high-contrast image with horizontal text lines, optionally rotated."""
    img = np.ones((800, 1200), dtype=np.uint8) * 255

    # Draw several distinct horizontal text lines
    for y in range(150, 700, 70):
        cv2.putText(
            img,
            "OFFICIAL ACADEMIC DEGREE VERIFICATION SYSTEM CERTIFICATE",
            (100, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            0,
            2,
            cv2.LINE_AA,
        )
        cv2.line(img, (100, y + 10), (1100, y + 10), 0, 2)

    if abs(angle_deg) > 1e-2:
        return rotate_image(img, angle_deg)
    return img


def test_straight_image_requires_no_skew_correction():
    img = create_synthetic_text_image(angle_deg=0.0)
    detected = estimate_skew_angle(img)
    assert abs(detected) < 0.5

    deskewer = Deskewer(min_threshold=0.5)
    deskewed, ctx = deskewer.process(img, {})
    assert ctx["applied_skew_angle"] == 0.0


def test_deskew_positive_rotation():
    target_angle = 15.0
    tilted = create_synthetic_text_image(angle_deg=target_angle)

    detected = estimate_skew_angle(tilted)
    # Estimated angle should match ground truth rotation within 0.8 degrees
    assert abs(detected - target_angle) < 0.8

    deskewer = Deskewer(min_threshold=0.2)
    deskewed, ctx = deskewer.process(tilted, {})
    assert abs(ctx["applied_skew_angle"] - target_angle) < 0.8

    # Residual skew in corrected image should be near 0
    residual = estimate_skew_angle(deskewed)
    assert abs(residual) < 0.5


def test_deskew_negative_rotation():
    target_angle = -10.0
    tilted = create_synthetic_text_image(angle_deg=target_angle)

    detected = estimate_skew_angle(tilted)
    assert abs(detected - target_angle) < 0.8

    deskewer = Deskewer(min_threshold=0.2)
    deskewed, ctx = deskewer.process(tilted, {})
    assert abs(ctx["applied_skew_angle"] - target_angle) < 0.8

    residual = estimate_skew_angle(deskewed)
    assert abs(residual) < 0.5
