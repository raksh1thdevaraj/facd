"""Unit tests for cryptographic HMAC digital signing and tamper detection (TC-REP-04)."""

from app.modules.report_generator.assembler import ReportAssembler
from app.modules.report_generator.signer import sign_report, verify_report_signature
from app.modules.score_fusion.service import ScoreFusionService
from app.schemas.decision import VerificationVerdict
from app.schemas.pipeline import CertificateFields


def test_sign_and_verify_valid_signature():
    """Verify digital signature roundtrip succeeds for untampered report (TC-REP-04)."""
    fusion = ScoreFusionService()
    decision = fusion.fuse_and_decide(
        certificate_id="cert-sign-001",
        visual_fake_prob=0.1,
        tabular_fake_prob=0.1,
        forensic_score=0.9,
        text_consistency_score=0.9,
        template_score=0.9,
    )

    report = ReportAssembler.assemble(
        certificate_id="cert-sign-001",
        decision=decision,
        extracted_fields=CertificateFields(register_number="REG-100"),
    )

    secret_key = "test-super-secret-key"
    sig = sign_report(report, secret_key)
    assert isinstance(sig, str)
    assert len(sig) == 64  # SHA-256 hex is 64 chars

    assert verify_report_signature(report, sig, secret_key) is True


def test_tamper_detection_on_altered_fields():
    """Verify modifying any core field immediately invalidates signature (TC-REP-04)."""
    fusion = ScoreFusionService()
    decision = fusion.fuse_and_decide(
        certificate_id="cert-sign-002",
        visual_fake_prob=0.9,
        tabular_fake_prob=0.9,
        forensic_score=0.3,
        text_consistency_score=0.3,
        template_score=0.2,
    )

    report = ReportAssembler.assemble(
        certificate_id="cert-sign-002",
        decision=decision,
        extracted_fields=CertificateFields(register_number="REG-200"),
    )

    secret_key = "test-super-secret-key"
    sig = sign_report(report, secret_key)

    # 1. Tamper with score
    tampered_report = report.model_copy(deep=True)
    tampered_report.authenticity_score = 0.99
    assert verify_report_signature(tampered_report, sig, secret_key) is False

    # 2. Tamper with verdict
    tampered_report2 = report.model_copy(deep=True)
    tampered_report2.verdict = VerificationVerdict.AUTHENTIC
    assert verify_report_signature(tampered_report2, sig, secret_key) is False

    # 3. Tamper with student roll number
    tampered_report3 = report.model_copy(deep=True)
    tampered_report3.extracted_fields.register_number = "REG-HACKED-999"
    assert verify_report_signature(tampered_report3, sig, secret_key) is False
