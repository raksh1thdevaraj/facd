"""Tests for Course Certificate QR Code Detection and Decoding."""

import cv2
import numpy as np
import pytest
import qrcode

from app.modules.course_verification.qr_detector import CourseQRDetector


@pytest.fixture
def qr_detector():
    return CourseQRDetector()


def create_qr_image(payload: str, size: int = 400) -> np.ndarray:
    """Helper creating high-fidelity QR code image array."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img_pil = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    arr = np.array(img_pil)
    # Embed inside larger white canvas
    canvas = np.ones((size + 200, size + 200, 3), dtype=np.uint8) * 255
    canvas[100 : 100 + arr.shape[0], 100 : 100 + arr.shape[1]] = arr
    return canvas


def test_standard_qr_detection(qr_detector):
    test_url = "https://coursera.org/verify/COURSE-XYZ-12345"
    img = create_qr_image(test_url)
    res = qr_detector.detect_and_decode(img)

    assert res.qr_detected is True
    assert res.qr_decoded is True
    assert res.payload == test_url


def test_rotated_qr_detection(qr_detector):
    test_url = "https://edx.org/certificates/9876543210abcdef"
    img = create_qr_image(test_url)

    # Rotate by 90 degrees
    rotated = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    res = qr_detector.detect_and_decode(rotated)

    assert res.qr_detected is True
    assert res.qr_decoded is True
    assert res.payload == test_url


def test_no_qr_image(qr_detector):
    blank_canvas = np.ones((500, 500, 3), dtype=np.uint8) * 255
    res = qr_detector.detect_and_decode(blank_canvas)

    assert res.qr_detected is False
    assert res.qr_decoded is False
    assert res.payload is None
