"""Tests for SSRF Protection and Issuer Domain Verification."""

import pytest

from app.modules.course_verification.url_verifier import CourseURLVerifier


@pytest.fixture
def url_verifier():
    return CourseURLVerifier()


def test_ssrf_blocked_destinations(url_verifier):
    """Ensure SSRF filter intercepts local, loopback, and cloud metadata addresses."""
    malicious_urls = [
        "http://127.0.0.1:8000/internal-admin",
        "http://localhost/secret",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/dashboard",
        "http://192.168.1.1/router",
    ]

    for url in malicious_urls:
        res = url_verifier.verify_url(url, check_accessibility=False)
        assert (
            res.risk_level == "MALICIOUS"
            or "SSRF" in (res.remarks or "")
            or "protected" in (res.error_message or "")
        )


def test_authoritative_issuer_domains(url_verifier):
    """Ensure authoritative issuers like Coursera and edX receive high trust scores."""
    valid_coursera = "https://coursera.org/verify/AB12CD34"
    res = url_verifier.verify_url(valid_coursera, check_accessibility=False)

    assert res.is_valid_url is True
    assert res.resolved_issuer == "Coursera"
    assert res.domain_match is True
    assert res.trust_score == 1.0


def test_suspicious_tld_recognition(url_verifier):
    """Ensure shady domains (e.g. .xyz, .top) are classified as SUSPICIOUS."""
    suspicious_url = "https://fake-coursera-cert.xyz/verify/123"
    res = url_verifier.verify_url(suspicious_url, check_accessibility=False)

    assert res.is_valid_url is True
    assert res.resolved_issuer is None
    assert res.risk_level == "SUSPICIOUS"
    assert res.trust_score <= 0.5
