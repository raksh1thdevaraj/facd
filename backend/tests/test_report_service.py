"""Integration tests for ReportService lifecycle and database persistence."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.report import VerificationReportModel
from app.modules.report_generator.service import ReportService
from app.modules.score_fusion.service import ScoreFusionService
from app.schemas.pipeline import CertificateFields


def test_report_service_end_to_end(tmp_path: Path):
    """Verify ReportService end-to-end generation, signing, and file archival."""
    service = ReportService(
        output_dir=tmp_path,
        secret_key="service-test-secret-key",
        base_url="http://localhost:8000",
    )

    fusion = ScoreFusionService()
    decision = fusion.fuse_and_decide(
        certificate_id="cert-serv-001",
        visual_fake_prob=0.05,
        tabular_fake_prob=0.05,
        forensic_score=0.95,
        text_consistency_score=0.98,
        template_score=0.95,
    )

    report = service.generate_report(
        certificate_id="cert-serv-001",
        decision=decision,
        extracted_fields=CertificateFields(
            student_name="Charlie Brown",
            register_number="REG-CB-007",
        ),
    )

    # 1. Assert file creations
    assert Path(report.pdf_path).exists()
    assert Path(report.json_path).exists()
    assert Path(report.qr_code_path).exists()

    # 2. Assert digital signature
    assert report.report_hmac_signature is not None
    assert service.verify_authenticity(report) is True

    # 3. Assert retrieval
    retrieved = service.get_report(report.report_id)
    assert retrieved is not None
    assert retrieved.report_id == report.report_id
    assert retrieved.extracted_fields.student_name == "Charlie Brown"

    # 4. Assert PDF path lookup
    pdf_lookup = service.get_pdf_path(report.report_id)
    assert pdf_lookup is not None
    assert pdf_lookup.exists()


def test_report_service_db_persistence(tmp_path: Path):
    """Verify report record is persisted and updated in relational database."""
    engine = create_engine(f"sqlite:///{tmp_path}/test_report_db.sqlite")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        service = ReportService(output_dir=tmp_path)
        fusion = ScoreFusionService()
        decision = fusion.fuse_and_decide(
            certificate_id="cert-db-report",
            visual_fake_prob=0.1,
            tabular_fake_prob=0.1,
            forensic_score=0.9,
            text_consistency_score=0.9,
            template_score=0.9,
        )

        report = service.generate_report(
            certificate_id="cert-db-report",
            decision=decision,
            db=session,
        )

        # Check DB row
        db_record = session.query(VerificationReportModel).filter_by(id=report.report_id).first()
        assert db_record is not None
        assert db_record.certificate_id == "cert-db-report"
        assert db_record.pdf_path == report.pdf_path
        assert db_record.json_path == report.json_path
        assert db_record.hmac_signature == report.report_hmac_signature

        # Retrieve via service using DB fallback
        retrieved = service.get_report(report.report_id, db=session)
        assert retrieved is not None
        assert retrieved.report_id == report.report_id
    finally:
        session.close()
