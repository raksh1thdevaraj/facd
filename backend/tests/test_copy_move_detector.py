import cv2
import numpy as np

from app.modules.forensics.copy_move_detector import CopyMoveDetector


def _draw_complex_stamp(canvas: np.ndarray, center_x: int, center_y: int, radius: int = 40) -> None:
    """Draw a feature-rich synthetic seal/stamp with concentric shapes and cross-hatching."""
    cv2.circle(canvas, (center_x, center_y), radius, (0, 0, 180), 2)
    cv2.circle(canvas, (center_x, center_y), radius - 8, (180, 0, 0), 1)
    cv2.circle(canvas, (center_x, center_y), radius - 16, (0, 150, 0), 2)

    # Draw starburst rays
    for angle in range(0, 360, 30):
        rad = np.deg2rad(angle)
        x1 = int(center_x + (radius - 24) * np.cos(rad))
        y1 = int(center_y + (radius - 24) * np.sin(rad))
        x2 = int(center_x + radius * np.cos(rad))
        y2 = int(center_y + radius * np.sin(rad))
        cv2.line(canvas, (x1, y1), (x2, y2), (50, 50, 50), 2)

    # Draw central emblem cross
    cv2.drawMarker(
        canvas,
        (center_x, center_y),
        (0, 0, 0),
        markerType=cv2.MARKER_TILTED_CROSS,
        markerSize=18,
        thickness=2,
    )


def test_clean_document_no_clones():
    """Verify clean image with standard text has copy_move_score 1.0 and 0 clone matches."""
    detector = CopyMoveDetector()

    canvas = np.full((600, 800, 3), 255, dtype=np.uint8)
    # Draw simple text lines
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(canvas, "UNIVERSITY OF OXFORD", (100, 150), font, 1.0, (0, 0, 0), 2)
    cv2.putText(canvas, "OFFICIAL DEGREE CERTIFICATE", (100, 250), font, 0.8, (0, 0, 0), 1)

    score, clones = detector.analyze(canvas)
    assert score == 1.0
    assert len(clones) == 0


def test_detects_cloned_signature_or_seal():
    """TC-FOR-02: Detect copy-move forgery when a complex stamp/seal is duplicated elsewhere."""
    detector = CopyMoveDetector()

    canvas = np.full((800, 800, 3), 255, dtype=np.uint8)

    # Draw source stamp at (150, 150)
    _draw_complex_stamp(canvas, 150, 150, radius=45)

    # Clone identical stamp to (500, 500) (displacement: dx=350, dy=350)
    _draw_complex_stamp(canvas, 500, 500, radius=45)

    score, clones = detector.analyze(canvas)

    assert score < 1.0
    assert len(clones) >= 1

    clone = clones[0]
    assert clone.inlier_count >= 5
    assert clone.confidence >= 0.70

    # Verify displacement vector is approximately dx=350, dy=350
    dx, dy = clone.displacement_vector
    assert abs(dx - 350.0) < 15.0
    assert abs(dy - 350.0) < 15.0
