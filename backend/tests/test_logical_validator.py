from app.modules.text_consistency.logical_validator import LogicalConsistencyValidator
from app.schemas.pipeline import CertificateFields
from app.schemas.primitives import CheckStatus
from app.schemas.text_consistency import AnomalyType


def test_valid_academic_fields_pass():
    """Verify that a legitimate certificate with valid dates and scores yields logical score 1.0."""
    validator = LogicalConsistencyValidator()

    fields = CertificateFields(
        student_name="Alice Smith",
        register_number="2020CS101",
        course_degree="Bachelor of Engineering",
        grade_or_marks="CGPA: 8.75 / 10.0",
        issue_date="2022-06-15",
    )

    score, anomalies, checks = validator.analyze(
        fields, raw_text="Graduated in 2022 with CGPA 8.75"
    )
    assert score >= 0.95
    assert len(anomalies) == 0

    # Verify check statuses
    for check in checks:
        assert check.status == CheckStatus.PASSED


def test_future_issue_date_triggers_penalty():
    """Verify that an issue date in the future (e.g., 2035) causes a severe penalty."""
    validator = LogicalConsistencyValidator()

    fields = CertificateFields(
        student_name="Bob Jones",
        register_number="2020CS102",
        course_degree="Master of Science",
        grade_or_marks="First Class",
        issue_date="2035-12-01",  # Future date
    )

    score, anomalies, checks = validator.analyze(fields, raw_text="Issued on 2035-12-01")
    assert score <= 0.40
    assert len(anomalies) >= 1

    future_anomaly = next(
        a for a in anomalies if a.anomaly_type == AnomalyType.LOGICAL_CONTRADICTION
    )
    assert "future" in future_anomaly.description
    assert future_anomaly.severity >= 0.95

    date_check = next(c for c in checks if c.rule_id == "RULE_DATE_CHRONOLOGY")
    assert date_check.status == CheckStatus.FAILED


def test_invalid_cgpa_scale_flagged():
    """Verify impossible CGPA (10.5 on 10.0 scale) triggers critical failure."""
    validator = LogicalConsistencyValidator()

    fields = CertificateFields(
        student_name="Charlie Brown",
        register_number="2020CS103",
        course_degree="Bachelor of Technology",
        grade_or_marks="CGPA 10.5",  # Impossible grade > 10.0
        issue_date="2021-05-10",
    )

    score, anomalies, checks = validator.analyze(fields, raw_text="Awarded CGPA 10.5")
    assert score <= 0.40
    assert len(anomalies) >= 1

    grade_anomaly = next(
        a for a in anomalies if a.anomaly_type == AnomalyType.LOGICAL_CONTRADICTION
    )
    assert "exceeds maximum scale" in grade_anomaly.description

    grade_check = next(c for c in checks if c.rule_id == "RULE_GRADE_BOUNDS")
    assert grade_check.status == CheckStatus.FAILED


def test_invalid_percentage_flagged():
    """Verify impossible percentage (> 100%) triggers logical contradiction."""
    validator = LogicalConsistencyValidator()

    fields = CertificateFields(
        student_name="David Miller",
        register_number="2020CS104",
        course_degree="Bachelor of Arts",
        grade_or_marks="Marks: 105%",
        issue_date="2020-07-20",
    )

    score, anomalies, checks = validator.analyze(fields, raw_text="Scored 105% in final year")
    assert score <= 0.40
    assert len(anomalies) >= 1

    grade_check = next(c for c in checks if c.rule_id == "RULE_GRADE_BOUNDS")
    assert grade_check.status == CheckStatus.FAILED


def test_honors_contradiction_flagged():
    """Verify contradiction between low marks (52%) and claimed 'Distinction'."""
    validator = LogicalConsistencyValidator()

    fields = CertificateFields(
        student_name="Eve White",
        register_number="2020CS105",
        course_degree="Bachelor of Commerce",
        grade_or_marks="52%",
        issue_date="2021-08-14",
    )

    score, anomalies, checks = validator.analyze(
        fields, raw_text="Secured 52% and awarded First Class with Distinction"
    )
    assert score <= 0.50
    assert len(anomalies) >= 1

    contradiction_anomaly = next(
        a for a in anomalies if a.anomaly_type == AnomalyType.LOGICAL_CONTRADICTION
    )
    assert "Contradiction between score" in contradiction_anomaly.description
