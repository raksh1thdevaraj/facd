"""
Synthetic Server Resilience & Error Recovery Unit Tests.
Verifies that the backend server handles corrupt uploads, 400/500 scenarios,
and health checks without terminating or dropping client sockets.
"""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check_endpoint(client):
    """Verify /health and /api/health return status ok with uptime."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["ok", "healthy"]
    assert "uptime" in data
    assert isinstance(data["uptime"], (int, float))

    # Also test /api/health
    api_res = client.get("/api/health")
    assert api_res.status_code == 200
    assert api_res.json()["status"] in ["ok", "healthy"]


def test_empty_upload_400_handling(client):
    """Verify that an empty file upload returns 400 JSON and does not crash server."""
    files = {"file": ("empty.png", b"", "image/png")}
    res = client.post("/verify", files=files, data={"certificate_type": "marks_card"})
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert "empty" in data["error"].lower()


def test_unsupported_file_extension_400_handling(client):
    """Verify that unsupported extensions return 400 JSON without crashing."""
    files = {"file": ("test.exe", b"MZDummyExecutableBytes", "application/octet-stream")}
    res = client.post("/verify", files=files, data={"certificate_type": "marks_card"})
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert "unsupported" in data["error"].lower()


def test_corrupt_image_payload_handling(client):
    """Verify corrupt image data returns 400 JSON without process termination."""
    corrupt_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRcorrupted-bytes-data-stream"
    files = {"file": ("corrupt.png", corrupt_bytes, "image/png")}
    res = client.post("/verify", files=files, data={"certificate_type": "marks_card"})
    assert res.status_code in [400, 422]
    data = res.json()
    assert data["success"] is False


def test_synthetic_valid_image_upload(client):
    """Verify that a valid synthesized image upload runs without error."""
    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    valid_bytes = buf.getvalue()

    files = {"file": ("test_cert.png", valid_bytes, "image/png")}
    res = client.post(
        "/verify",
        files=files,
        data={
            "certificate_type": "marks_card",
            "expected_student_name": "Test Student",
            "expected_reg_no": "TEST12345",
        },
    )
    # Regardless of whether verdict is authentic or suspicious, server must return 200 JSON
    assert res.status_code == 200
    data = res.json()
    assert "final_status" in data or "is_authentic" in data
