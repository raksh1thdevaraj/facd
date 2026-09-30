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


def test_concurrent_health_and_status_during_verification(client):
    """Verify that dashboard health and status queries respond concurrently without blocking."""
    import concurrent.futures

    img = Image.new("RGB", (100, 100), color=(250, 250, 250))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    valid_bytes = buf.getvalue()

    def _call_verify():
        files = {"file": ("concurrent_test.png", valid_bytes, "image/png")}
        return client.post(
            "/verify",
            files=files,
            data={"certificate_type": "marks_card"},
        )

    def _call_health():
        return client.get("/health")

    def _call_status():
        return client.get("/status")

    def _call_history():
        return client.get("/api/verifications/history")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # Launch verify
        verify_fut = executor.submit(_call_verify)
        # Concurrently query health, status, and history
        health_fut = executor.submit(_call_health)
        status_fut = executor.submit(_call_status)
        history_fut = executor.submit(_call_history)

        health_res = health_fut.result(timeout=10)
        status_res = status_fut.result(timeout=10)
        history_res = history_fut.result(timeout=10)
        verify_res = verify_fut.result(timeout=60)

    assert health_res.status_code == 200
    assert status_res.status_code == 200
    assert history_res.status_code == 200
    assert verify_res.status_code == 200


def test_live_url_timeout_fallback_resilience():
    """Verify that an external URL scrape timeout returns TIMEOUT_FALLBACK without crashing."""
    from unittest.mock import patch
    import httpx
    from app.services.live_url_verifier import LiveURLVerifier

    verifier = LiveURLVerifier()
    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("Connection timed out")):
        res = verifier.verify_live_url("https://coursera.org/verify/FAKE1234")

    assert res["executed"] is True
    assert res["url_status"] == "TIMEOUT_FALLBACK"
    assert res["is_valid"] is True
    assert res["is_mismatch"] is False
    assert "timed out" in res["reason"].lower()

