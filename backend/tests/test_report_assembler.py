"""Unit tests for ReportAssembler and FullVerificationReport schema (TC-REP-01)."""

from datetime import datetime

from app.modules.report_generator.assembler import ReportAssembler
from app.modules.score_fusion.service import ScoreFusionService
from app.schemas.decision import VerificationVerdict
from app.schemas.pipeline import CertificateFields, VerificationReportDTO
from app.schemas.report import FileMetadata, FullVerificationReport


def test_report_assembler_populates_all_fields():
    """Verify assembler populates all metadata, scores, and converts to DTO (TC-REP-01)."""
    fusion = ScoreFusionService()
    decision = fusion.fuse_and_decide(
        certificate_id="cert-asm-001",
        visual_fake_prob=0.05,
        tabular_fake_prob=0.08,
        forensic_score=0.90,
        text_consistency_score=0.95,
        template_score=0.92,
        tier_status="TIER_1_VERIFIED",
    )

    fields = CertificateFields(
        student_name="Alice Smith",
        register_number="REG-2024-001",
        institution_name="National Institute",
        course_degree="B.Tech Computer Science",
        grade_or_marks="Distinction",
        issue_date="2024-06-15",
        certificate_number="CERT-001-A",
    )

    meta = FileMetadata(
        filename="alice_degree.png",
        file_size_kb=450.0,
        file_format="PNG",
        sha256_checksum="abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        upload_timestamp=datetime.utcnow(),
    )

    report = ReportAssembler.assemble(
        certificate_id="cert-asm-001",
        decision=decision,
        file_metadata=meta,
        extracted_fields=fields,
        verifier_username="Auditor Alice",
        base_url="https://verify.university.edu",
    )

    assert isinstance(report, FullVerificationReport)
    assert report.certificate_id == "cert-asm-001"
    assert report.verdict == VerificationVerdict.AUTHENTIC
    assert report.authenticity_percentage > 90.0
    assert report.extracted_fields.student_name == "Alice Smith"
    assert report.extracted_fields.register_number == "REG-2024-001"
    assert len(report.subsystem_scores) >= 5
    assert (
        report.verification_url == f"https://verify.university.edu/verify-report/{report.report_id}"
    )

    # Verify SPEC-02 DTO mapping
    dto = report.to_dto()
    assert isinstance(dto, VerificationReportDTO)
    assert dto.document_id == "cert-asm-001"
    assert dto.summary_verdict == "AUTHENTIC"
    assert dto.extracted_fields.student_name == "Alice Smith"
