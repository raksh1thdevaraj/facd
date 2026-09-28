"""
Unit and integration tests for Google Gemini Vision Forensic Verifier.
Tests service initialization, prompt structure, image payload preparation,
graceful degradation, and controller integration on `/api/verify`.
"""

import json
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.geminiVerifier import (
    GeminiVerifier,
)


@pytest.fixture
def dummy_certificate_image() -> np.ndarray:
    """Generate a clean synthetic certificate image array."""
    img = np.ones((600, 800, 3), dtype=np.uint8) * 255
    # Draw simple header border
    img[20:30, :] = [50, 50, 50]
    return img


@pytest.fixture
def mock_gemini_response_json() -> str:
    """Standard forensic JSON payload returned by Gemini Vision."""
    return json.dumps(
        {
            "entities": {
                "student_name": "Aarav Sharma",
                "registration_no": "HTU2022-CS-041",
                "cgpa_or_score": "8.85",
                "issuing_institution": "Heritage Technical University",
                "degree_or_program": "B.Tech Computer Science",
                "issue_date": "2024-06-15",
            },
            "forgery_indicators": {
                "font_mismatch": False,
                "text_baseline_shift": False,
                "patch_compression_artifacts": False,
                "splicing_detected": False,
                "details": "Consistent typography, uniform pixel density, no baseline displacement.",
            },
            "arithmetic_consistency": {
                "is_consistent": True,
                "details": "Semester credits and grade point averages align mathematically.",
            },
            "is_authentic": True,
            "confidence_score": 0.96,
            "verdict": "VERIFIED",
            "forensic_summary": "Document exhibits visual and typographic integrity.",
        }
    )


def test_gemini_verifier_initialization():
    """Verify GeminiVerifier initializes with correct defaults and models."""
    verifier = GeminiVerifier(api_key="test-key-12345", model="gemini-2.5-flash")
    assert verifier.api_key == "test-key-12345"
    assert verifier.primary_model == "gemini-2.5-flash"
    assert verifier.timeout_ms == 30000


def test_gemini_verifier_missing_key_degrades_gracefully(dummy_certificate_image):
    """When API key is empty, verifier should return SKIPPED without raising exceptions."""
    verifier = GeminiVerifier(api_key="", model="gemini-2.5-flash")
    assert not verifier.is_available

    result = verifier.verify(image_input=dummy_certificate_image)
    assert result["success"] is False
    assert result["status"] == "SKIPPED"
    assert result["error"] == "GEMINI_API_KEY_NOT_CONFIGURED"
    assert "forensic_summary" in result


def test_prepare_image_bytes_formats(dummy_certificate_image, tmp_path):
    """Verify image preparation handles numpy arrays, file paths, and raw bytes."""
    verifier = GeminiVerifier(api_key="test-key", model="gemini-2.5-flash")

    # 1. Test numpy array
    bytes_arr, mime_arr = verifier._prepare_image_bytes(dummy_certificate_image)
    assert isinstance(bytes_arr, bytes)
    assert mime_arr == "image/png"
    assert bytes_arr.startswith(b"\x89PNG")

    # 2. Test file path
    temp_file = tmp_path / "cert.png"
    temp_file.write_bytes(bytes_arr)
    bytes_file, mime_file = verifier._prepare_image_bytes(temp_file)
    assert bytes_file == bytes_arr
    assert mime_file == "image/png"

    # 3. Test raw JPEG bytes
    jpeg_dummy = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    bytes_raw, mime_raw = verifier._prepare_image_bytes(jpeg_dummy)
    assert bytes_raw == jpeg_dummy
    assert mime_raw == "image/jpeg"

    # 4. Test invalid path raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        verifier._prepare_image_bytes(tmp_path / "non_existent.png")


def test_gemini_verifier_successful_mocked_inference(
    dummy_certificate_image, mock_gemini_response_json
):
    """Verify end-to-end verification logic with mocked Gemini API client."""
    verifier = GeminiVerifier(api_key="mock-api-key", model="gemini-2.5-flash")

    mock_client = MagicMock()
    mock_response = MagicMock()
    # Test with markdown fences to verify clean JSON stripping
    mock_response.text = f"```json\n{mock_gemini_response_json}\n```"
    mock_client.models.generate_content.return_value = mock_response

    verifier._client = mock_client

    result = verifier.verify(
        image_input=dummy_certificate_image,
        certificate_type="marks_card",
        expected_student_name="Aarav Sharma",
        expected_reg_no="HTU2022-CS-041",
    )

    assert result["success"] is True
    assert result["status"] == "COMPLETED"
    assert result["is_authentic"] is True
    assert result["confidence_score"] == 0.96
    assert result["verdict"] == "VERIFIED"
    assert result["entities"]["student_name"] == "Aarav Sharma"
    assert result["entities"]["registration_no"] == "HTU2022-CS-041"
    assert result["forgery_indicators"]["font_mismatch"] is False
    assert result["arithmetic_consistency"]["is_consistent"] is True


def test_gemini_verifier_tampering_flagged(dummy_certificate_image):
    """Verify when Gemini flags forgery, it reflects in structured output."""
    verifier = GeminiVerifier(api_key="mock-api-key", model="gemini-2.5-flash")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(
        {
            "entities": {"student_name": "John Doe", "registration_no": "FAKE-101"},
            "forgery_indicators": {
                "font_mismatch": True,
                "text_baseline_shift": True,
                "patch_compression_artifacts": True,
                "splicing_detected": True,
                "details": "Clear rectangular splicing artifact around CGPA 9.8.",
            },
            "arithmetic_consistency": {
                "is_consistent": False,
                "details": "Sum of semester GPAs does not calculate to stated CGPA.",
            },
            "is_authentic": False,
            "confidence_score": 0.12,
            "verdict": "REJECTED",
            "forensic_summary": "Extensive tampering detected in grade boxes.",
        }
    )
    mock_client.models.generate_content.return_value = mock_response
    verifier._client = mock_client

    result = verifier.verify(dummy_certificate_image)
    assert result["success"] is True
    assert result["is_authentic"] is False
    assert result["verdict"] == "REJECTED"
    assert result["forgery_indicators"]["font_mismatch"] is True
    assert result["forgery_indicators"]["splicing_detected"] is True
    assert result["arithmetic_consistency"]["is_consistent"] is False


def test_gemini_verifier_server_error_fallback(dummy_certificate_image):
    """Verify handling when all Gemini candidate models return 503 or errors."""
    verifier = GeminiVerifier(api_key="mock-api-key", model="gemini-2.5-flash")

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("503 UNAVAILABLE: High demand")
    verifier._client = mock_client

    result = verifier.verify(dummy_certificate_image)
    assert result["success"] is False
    assert result["status"] == "DEGRADED"
    assert "High demand" in result["error"]
    assert result["verdict"] == "UNVERIFIED"


def test_controller_api_verify_with_gemini(dummy_certificate_image, mock_gemini_response_json):
    """Test primary `/api/verify` upload route incorporates Gemini and file metadata."""
    import io

    import cv2

    # Prepare PNG bytes
    _, buf = cv2.imencode(".png", dummy_certificate_image)
    file_bytes = buf.tobytes()

    client = TestClient(app)

    # Mock the Gemini verifier inside verification_hub
    with patch("app.api.v1.endpoints.verification_hub.get_gemini_verifier") as mock_get_v:
        mock_v_instance = MagicMock()
        mock_v_instance.verify.return_value = {
            "success": True,
            "status": "COMPLETED",
            "model_used": "gemini-2.5-flash",
            "is_authentic": True,
            "confidence_score": 0.95,
            "verdict": "VERIFIED",
            "entities": {
                "student_name": "Aarav Sharma",
                "registration_no": "HTU2022-CS-041",
                "cgpa_or_score": "8.85",
                "issuing_institution": "Heritage Technical University",
            },
            "forgery_indicators": {
                "font_mismatch": False,
                "text_baseline_shift": False,
                "patch_compression_artifacts": False,
                "splicing_detected": False,
                "details": "Consistent typography.",
            },
            "arithmetic_consistency": {
                "is_consistent": True,
                "details": "Calculations mathematically consistent.",
            },
            "forensic_summary": "Passed Gemini Vision audit.",
        }
        mock_get_v.return_value = mock_v_instance

        # Test POST /api/verify
        response = client.post(
            "/api/verify",
            files={"file": ("certificate.png", io.BytesIO(file_bytes), "image/png")},
            data={"certificate_type": "marks_card"},
        )

        assert response.status_code == 200
        payload = response.json()

        # Contract asserts
        assert payload["success"] is True
        assert "details" in payload
        assert "file_metadata" in payload["details"]
        assert payload["details"]["file_metadata"]["filename"] == "certificate.png"
        assert payload["details"]["gemini_verified"] is True
        assert "gemini_analysis" in payload["details"]
        assert payload["details"]["gemini_analysis"]["model_used"] == "gemini-2.5-flash"

        # Forensic cards asserts
        assert "forensic_cards" in payload
        assert "gemini_vision" in payload["forensic_cards"]
        assert payload["forensic_cards"]["gemini_vision"]["success"] is True
        assert payload["forensic_cards"]["gemini_vision"]["verdict"] == "VERIFIED"
