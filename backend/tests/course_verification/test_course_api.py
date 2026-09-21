"""Integration tests for Course Certificate Verification API Endpoints."""

import cv2
import numpy as np
import pytest
import qrcode
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def generate_test_certificate_image(
    qr_url: str = "https://coursera.org/verify/UC-12345678",
) -> bytes:
    """Create synthetic certificate JPEG bytes containing a real QR code."""
    canvas = np.ones((800, 1100, 3), dtype=np.uint8) * 250
    cv2.putText(
        canvas,
        "CERTIFICATE OF COMPLETION",
        (250, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (20, 30, 40),
        3,
    )
    cv2.putText(
        canvas,
        "This is to certify that Alice Johnson has successfully completed",
        (150, 240),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (40, 40, 40),
        2,
    )
    cv2.putText(
        canvas,
        "Machine Learning Specialization",
        (280, 320),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (15, 80, 20),
        3,
    )
    cv2.putText(
        canvas,
        "Certificate ID: UC-12345678",
        (150, 420),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (60, 60, 60),
        2,
    )

    # Embed QR Code
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = np.array(qr.make_image(fill_color="black", back_color="white").convert("RGB"))
    canvas[500 : 500 + qr_img.shape[0], 150 : 150 + qr_img.shape[1]] = qr_img

    _, encoded = cv2.imencode(".png", canvas)
    return encoded.tobytes()


def test_list_issuers_api(client):
    response = client.get("/api/v1/course-certificates/issuers/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    assert any(i["name"] == "Coursera" for i in data)


def test_verify_url_api(client):
    response = client.post(
        "/api/v1/course-certificates/verify-url",
        json={"url": "https://coursera.org/verify/VALID123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid_url"] is True
    assert data["resolved_issuer"] == "Coursera"
    assert data["risk_level"] == "SAFE"


def test_verify_course_certificate_api_flow(client):
    """Test upload, verify, query, and PDF report download."""
    img_bytes = generate_test_certificate_image()

    # 1. Upload & Verify
    upload_res = client.post(
        "/api/v1/course-certificates/verify",
        files={"file": ("coursera_test_cert.png", img_bytes, "image/png")},
    )
    assert upload_res.status_code == 200
    verify_data = upload_res.json()

    assert "verification_id" in verify_data
    assert "decision" in verify_data
    assert verify_data["decision"]["status"] in [
        "VERIFIED",
        "SUSPICIOUS",
        "FRAUDULENT",
        "UNVERIFIED",
    ]
    assert "extracted_fields" in verify_data
    assert "qr_result" in verify_data

    verif_id = verify_data["verification_id"]

    # 2. Get Audit Record
    get_res = client.get(f"/api/v1/course-certificates/{verif_id}")
    assert get_res.status_code == 200
    record_data = get_res.json()
    assert record_data["id"] == verif_id

    # 3. Download PDF Report
    pdf_res = client.get(f"/api/v1/course-certificates/{verif_id}/report")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000
