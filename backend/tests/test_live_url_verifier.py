"""
Unit tests for Live Institutional URL Cross-Verification (Web Scraping & Truth-Check).
Verifies:
1. URL sanitization on OCR-distorted strings.
2. Token extraction for Coursera and institutional providers.
3. Identity mismatch detection: Visual 'VIRAT KOHLI' vs Official 'RISHI R K' -> FRAUDULENT (0.05).
4. Authentic credential validation.
5. 404 / Non-existent credential rejection -> FRAUDULENT (0.05).
"""

from unittest.mock import MagicMock, patch

import pytest
from app.services.live_url_verifier import LiveURLVerifier, get_live_url_verifier


@pytest.fixture
def verifier() -> LiveURLVerifier:
    return get_live_url_verifier()


def test_sanitize_ocr_fragmented_url(verifier: LiveURLVerifier):
    raw_ocr = "https://cour  ser a.or  g /v er if y /ST4861PPAN5J."
    clean = verifier.sanitize_url(raw_ocr)
    assert clean == "https://coursera.org/verify/ST4861PPAN5J"

    raw_ocr_2 = "coursera.org / verify / specialization / KKG64CU0L503"
    clean_2 = verifier.sanitize_url(raw_ocr_2)
    assert clean_2 == "https://coursera.org/verify/specialization/KKG64CU0L503"


def test_extract_token_from_url(verifier: LiveURLVerifier):
    t1 = verifier.extract_token_from_url("https://coursera.org/verify/ST4861PPAN5J")
    assert t1 == "ST4861PPAN5J"

    t2 = verifier.extract_token_from_url("https://coursera.org/verify/specialization/KKG64CU0L503")
    assert t2 == "KKG64CU0L503"

    t3 = verifier.extract_token_from_url("https://nptel.ac.in/noc/Ecertificate/?q=NPTEL23CS12S1")
    assert t3 == "NPTEL23CS12S1"


def test_identity_mismatch_fraud_detection(verifier: LiveURLVerifier):
    """
    Test identity-swapped fake certificate:
    The visual document displays 'VIRAT KOHLI', but the Coursera registry records 'RISHI R K'.
    Must flag IDENTITY_MISMATCH_FRAUD, verdict FRAUDULENT, and confidence 0.05 (5.0%).
    """
    mock_html = """
    <html>
      <body>
        <main>
          <div>
            <h3>Completed by<strong>RISHI R K</strong></h3>
            <h2>Project Planning and Productivity Mastery</h2>
            <p>September 19, 2026</p>
          </div>
        </main>
      </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://coursera.org/verify/ST4861PPAN5J"
    mock_resp.text = mock_html

    with patch("httpx.Client.get", return_value=mock_resp):
        res = verifier.verify_live_url(
            url="https://coursera.org/verify/ST4861PPAN5J",
            visual_student_name="VIRAT KOHLI",
            visual_course_title="Project Planning and Productivity Mastery",
        )

    assert res["executed"] is True
    assert res["is_mismatch"] is True
    assert res["mismatch_flag"] == "IDENTITY_MISMATCH_FRAUD"
    assert res["verdict"] == "FRAUDULENT"
    assert res["confidence_score"] == 0.05
    assert "VIRAT KOHLI" in res["discrepancy_details"]
    assert "RISHI R K" in res["discrepancy_details"]
    assert res["web_registered_name"] == "RISHI R K"


def test_authentic_credential_verification(verifier: LiveURLVerifier):
    """
    Test authentic certificate:
    Visual document displays 'RISHI R K', matching Coursera registry 'RISHI R K'.
    Must return AUTHENTIC with >= 0.95 confidence.
    """
    mock_html = """
    <html>
      <body>
        <main>
          <div>
            <h3>Completed by<strong>RISHI R K</strong></h3>
            <h2>Project Planning and Productivity Mastery</h2>
            <p>September 19, 2026</p>
          </div>
        </main>
      </body>
    </html>
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://coursera.org/verify/ST4861PPAN5J"
    mock_resp.text = mock_html

    with patch("httpx.Client.get", return_value=mock_resp):
        res = verifier.verify_live_url(
            url="https://coursera.org/verify/ST4861PPAN5J",
            visual_student_name="RISHI R K",
            visual_course_title="Project Planning and Productivity Mastery",
        )

    assert res["executed"] is True
    assert res["is_mismatch"] is False
    assert res["mismatch_flag"] is None
    assert res["verdict"] == "AUTHENTIC"
    assert res["confidence_score"] == 0.99
    assert res["web_registered_name"] == "RISHI R K"


def test_invalid_url_404_handling(verifier: LiveURLVerifier):
    """
    Test counterfeit/tampered verification URL (404 Not Found).
    Must flag INVALID_URL_404, verdict FRAUDULENT, and confidence 0.05.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.url = "https://coursera.org/verify/ST4861PPAN5J1"
    mock_resp.text = "Not Found"

    with patch("httpx.Client.get", return_value=mock_resp):
        res = verifier.verify_live_url(
            url="https://coursera.org/verify/ST4861PPAN5J1",
            visual_student_name="VIRAT KOHLI",
        )

    assert res["executed"] is True
    assert res["is_mismatch"] is True
    assert res["mismatch_flag"] == "INVALID_URL_404"
    assert res["verdict"] == "FRAUDULENT"
    assert res["confidence_score"] == 0.05
