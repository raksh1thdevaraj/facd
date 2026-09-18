import cv2
import numpy as np

from app.modules.preprocessing.perspective_warper import (
    PerspectiveWarper,
    find_document_corners,
    four_point_transform,
    order_points,
)


def test_order_points_canonical_ordering():
    pts = np.array([[200, 100], [50, 50], [50, 300], [220, 290]], dtype="float32")
    ordered = order_points(pts)

    # Top-left should be (50, 50)
    assert np.allclose(ordered[0], [50, 50])
    # Top-right should be (200, 100)
    assert np.allclose(ordered[1], [200, 100])
    # Bottom-right should be (220, 290)
    assert np.allclose(ordered[2], [220, 290])
    # Bottom-left should be (50, 300)
    assert np.allclose(ordered[3], [50, 300])


def test_four_point_transform_recovers_rectangle():
    # 500x500 square canvas
    img = np.zeros((600, 600, 3), dtype=np.uint8)
    # Draw an off-angle quadrilateral with distinct fill
    quad = np.array([[100, 80], [450, 120], [420, 500], [120, 480]], dtype=np.int32)
    cv2.fillPoly(img, [quad], (255, 255, 255))

    warped = four_point_transform(img, quad.astype("float32"))
    h, w = warped.shape[:2]

    # Warped result should be approximately rectangular (~350-400px wide and ~400px tall)
    assert 300 <= w <= 450
    assert 350 <= h <= 450
    # Center should be pure white
    assert np.all(warped[h // 2, w // 2] == 255)


def test_find_document_corners_on_synthetic_photo():
    # Dark desk background
    canvas = np.ones((1000, 1400, 3), dtype=np.uint8) * 40

    # Bright white certificate placed on the desk with perspective distortion
    cert_corners = np.array([[250, 150], [1150, 200], [1050, 850], [200, 800]], dtype=np.int32)
    cv2.fillPoly(canvas, [cert_corners], (245, 245, 245))
    # Add text inside certificate
    cv2.putText(
        canvas,
        "Bachelor of Science in Engineering",
        (350, 400),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (20, 20, 20),
        2,
    )

    detected = find_document_corners(canvas, min_area_ratio=0.25)
    assert detected is not None
    assert len(detected) == 4

    warper = PerspectiveWarper(enabled=True)
    rectified, ctx = warper.process(canvas, {})
    assert ctx["perspective_corrected"] is True
    assert rectified.shape[0] > 500
    assert rectified.shape[1] > 700


def test_flatbed_scan_falls_back_gracefully():
    # Already edge-to-edge certificate scan without external desk background
    scan = np.ones((800, 1200, 3), dtype=np.uint8) * 240
    cv2.putText(
        scan,
        "Official Certificate",
        (200, 400),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        (10, 10, 10),
        2,
    )

    warper = PerspectiveWarper(enabled=True, min_area_ratio=0.95)
    result, ctx = warper.process(scan, {})

    # When no distinct background boundary exists, falls back to original scan
    assert ctx["perspective_corrected"] is False
    assert result.shape == scan.shape
