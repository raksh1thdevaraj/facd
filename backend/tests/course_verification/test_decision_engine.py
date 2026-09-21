"""Tests for Course Verification Multi-Signal Decision Engine."""

import pytest
from app.modules.course_verification.decision_engine import CourseDecisionEngine
from app.schemas.course_certificate import (
    CourseComparisonResult,
    CourseForensicResult,
    CourseOnlineRecord,
    CourseQRResult,
    CourseSealSignatureResult,
    CourseURLVerificationResult,
    CourseVerificationStatus,
)


@pytest.fixture
def decision_engine():
    return CourseDecisionEngine()


def test_verified_verdict(decision_engine):
    """Clean certificate matching authoritative issuer with online confirmation -> VERIFIED."""
    qr_res = CourseQRResult(qr_detected=True, qr_decoded=True, payload="https://coursera.org/verify/123")
    url_res = CourseURLVerificationResult(
        is_valid_url=True,
        resolved_issuer="Coursera",
        trust_score=1.0,
        domain_match=True,
        is_known_issuer=True,
    )
    comp_res = CourseComparisonResult(
        name_match_score=0.98,
        course_match_score=0.95,
        cert_id_match_score=1.0,
        date_match_score=0.95,
        overall_match_score=0.97,
        online_record=CourseOnlineRecord(is_available=True),
        copied_qr_detected=False,
    )
    forensic_res = CourseForensicResult(
        tampering_detected=False,
        tampering_probability=0.08,
        copy_move_detected=False,
        noise_inconsistency_score=0.05,
    )

    decision = decision_engine.evaluate(
        ocr_confidence=0.92,
        qr_result=qr_res,
        url_result=url_res,
        comparison_result=comp_res,
        forensic_result=forensic_res,
    )

    assert decision.status == CourseVerificationStatus.VERIFIED
    assert decision.overall_authenticity_score >= 0.80
    assert decision.fraud_risk_score <= 0.25


def test_copied_qr_attack_forces_fraudulent(decision_engine):
    """Copied QR attack MUST unconditionally trigger FRAUDULENT verdict."""
    qr_res = CourseQRResult(qr_detected=True, qr_decoded=True, payload="https://coursera.org/verify/123")
    url_res = CourseURLVerificationResult(is_valid_url=True, trust_score=1.0)
    comp_res = CourseComparisonResult(
        name_match_score=0.15,
        course_match_score=0.20,
        overall_match_score=0.20,
        online_record=CourseOnlineRecord(is_available=True),
        copied_qr_detected=True,
    )
    forensic_res = CourseForensicResult(tampering_probability=0.10)

    decision = decision_engine.evaluate(
        ocr_confidence=0.90,
        qr_result=qr_res,
        url_result=url_res,
        comparison_result=comp_res,
        forensic_result=forensic_res,
    )

    assert decision.status == CourseVerificationStatus.FRAUDULENT
    assert decision.fraud_risk_score >= 0.90
    assert any("Transplanted QR" in r or "Copied" in r for r in decision.decision_reasons)


def test_network_unreachable_yields_unverified_not_fraudulent(decision_engine):
    """CRITICAL SPEC REQUIREMENT: Network or web accessibility failure must NOT trigger FRAUDULENT!"""
    qr_res = CourseQRResult(qr_detected=True, qr_decoded=True, payload="https://coursera.org/verify/123")
    url_res = CourseURLVerificationResult(is_valid_url=True, is_known_issuer=True, trust_score=1.0)
    # Online record was NOT available because issuer site timed out
    comp_res = CourseComparisonResult(
        online_record=None,
        copied_qr_detected=False,
    )
    forensic_res = CourseForensicResult(
        tampering_detected=False,
        tampering_probability=0.12,
        copy_move_detected=False,
    )

    decision = decision_engine.evaluate(
        ocr_confidence=0.88,
        qr_result=qr_res,
        url_result=url_res,
        comparison_result=comp_res,
        forensic_result=forensic_res,
    )

    assert decision.status == CourseVerificationStatus.UNVERIFIED
    assert decision.status != CourseVerificationStatus.FRAUDULENT
