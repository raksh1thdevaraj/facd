"""Tests for Cross-Modal Field Matching and Copied QR Attack Detection."""

import pytest
from app.modules.course_verification.comparator import CourseRecordComparator
from app.schemas.course_certificate import (
    CourseExtractedFields,
    CourseOnlineRecord,
)


@pytest.fixture
def comparator():
    return CourseRecordComparator()


def test_perfect_field_alignment(comparator):
    extracted = CourseExtractedFields(
        candidate_name="Alice Johnson",
        course_name="Machine Learning Specialization",
        certificate_id="ML-99210",
        issue_date="2024-05-15",
        issuer="Coursera",
    )

    online = CourseOnlineRecord(
        is_available=True,
        candidate_name="Alice Johnson",
        course_name="Machine Learning Specialization",
        certificate_id="ML-99210",
        issue_date="2024-05-15",
        issuer="Coursera",
    )

    res = comparator.compare_records(extracted, online)
    assert res.overall_match_score >= 0.95
    assert res.copied_qr_detected is False
    assert len(res.discrepancies) == 0


def test_copied_qr_attack_interception(comparator):
    """Critical Spec Test: Valid QR code with valid online record, but recipient name is completely different!"""
    # Forger pasted a valid QR of 'Bob Smith' onto a cert declaring 'Eve Forger'
    extracted = CourseExtractedFields(
        candidate_name="Eve Forger",
        course_name="Deep Learning Specialization",
        certificate_id="UC-883921",
        issuer="Coursera",
    )

    online = CourseOnlineRecord(
        is_available=True,
        candidate_name="Bob Smith",
        course_name="Deep Learning Specialization",
        certificate_id="UC-883921",
        issuer="Coursera",
    )

    res = comparator.compare_records(extracted, online)
    assert res.copied_qr_detected is True
    assert any("Recipients do not match" in d for d in res.discrepancies)
