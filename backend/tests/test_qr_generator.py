"""Unit tests for report QR code generator (TC-REP-03)."""

from pathlib import Path

import cv2

from app.modules.report_generator.qr_generator import generate_report_qr


def test_qr_code_generation_and_decoding(tmp_path: Path):
    """Verify QR generator writes valid PNG and decodes to verification URL (TC-REP-03)."""
    report_id = "test-report-uuid-999"
    base_url = "https://verify.academics.org"

    qr_path = generate_report_qr(
        report_id=report_id,
        base_url=base_url,
        output_dir=tmp_path,
    )

    assert qr_path.exists()
    assert qr_path.is_file()
    assert qr_path.suffix == ".png"

    # Decode with OpenCV QRCodeDetector
    img = cv2.imread(str(qr_path))
    assert img is not None

    detector = cv2.QRCodeDetector()
    decoded_text, points, _ = detector.detectAndDecode(img)

    assert decoded_text == f"{base_url}/verify-report/{report_id}"
