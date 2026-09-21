"""Integration tests for async pipeline orchestration and error rollbacks (TC-API-03, TC-API-04)."""

from pathlib import Path

import pytest
from PIL import Image
from sqlalchemy.orm import Session

from app.models.certificate import CertificateModel
from app.models.forensic import ForensicFindingModel
from app.models.ml_prediction import MLPredictionModel
from app.models.ocr_field import OCRFieldModel
from app.models.report import VerificationReportModel
from app.models.template import TemplateMatchResultModel
from app.models.text_consistency import TextConsistencyModel
from app.services.pipeline_orchestrator import VerificationPipelineOrchestrator


def test_async_pipeline_executes_to_completion(tmp_path: Path, db_session: Session):
    """Verify orchestrator runs 10 stages and populates all database tables (TC-API-03)."""
    # 1. Create valid dummy certificate image
    img_path = tmp_path / "valid_cert.png"
    Image.new("RGB", (800, 600), color=(245, 245, 245)).save(img_path)

    cert_id = "cert-pipe-001"
    cert = CertificateModel(
        id=cert_id,
        file_path=str(img_path),
        file_hash="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        original_filename="valid_cert.png",
        file_size=img_path.stat().st_size,
        mime_type="image/png",
        job_status="PENDING",
        job_progress=0,
    )
    db_session.add(cert)
    db_session.commit()

    # 2. Run Pipeline Orchestrator
    orchestrator = VerificationPipelineOrchestrator()
    report = orchestrator.run_pipeline(certificate_id=cert_id, db=db_session)

    # 3. Assert Certificate job status completed
    db_session.refresh(cert)
    assert cert.job_status == "COMPLETED"
    assert cert.job_progress == 100
    assert cert.job_error is None

    # 4. Assert all child result tables were populated
    ocr_rows = db_session.query(OCRFieldModel).filter_by(certificate_id=cert_id).all()
    assert len(ocr_rows) > 0

    consistency = db_session.query(TextConsistencyModel).filter_by(certificate_id=cert_id).first()
    assert consistency is not None
    assert consistency.overall_score > 0.0

    forensics = db_session.query(ForensicFindingModel).filter_by(certificate_id=cert_id).all()
    assert len(forensics) > 0

    template = db_session.query(TemplateMatchResultModel).filter_by(certificate_id=cert_id).first()
    assert template is not None

    ml_pred = db_session.query(MLPredictionModel).filter_by(certificate_id=cert_id).first()
    assert ml_pred is not None

    verif_rep = db_session.query(VerificationReportModel).filter_by(certificate_id=cert_id).first()
    assert verif_rep is not None
    assert verif_rep.verdict == report.verdict.value


def test_database_rollback_on_pipeline_error(db_session: Session):
    """Verify uncommitted transactions rollback and job_status is FAILED on fault (TC-API-04)."""
    cert_id = "cert-pipe-fault"
    cert = CertificateModel(
        id=cert_id,
        file_path="/nonexistent/missing_file_path.png",  # Guaranteed fault
        file_hash="deadbeef",
        original_filename="faulty.png",
        file_size=0,
        job_status="PENDING",
        job_progress=0,
    )
    db_session.add(cert)
    db_session.commit()

    orchestrator = VerificationPipelineOrchestrator()

    with pytest.raises(FileNotFoundError):
        orchestrator.run_pipeline(certificate_id=cert_id, db=db_session)

    # Verify status is FAILED in database
    db_session.refresh(cert)
    assert cert.job_status == "FAILED"
    assert cert.job_error is not None
    assert "missing at" in cert.job_error
