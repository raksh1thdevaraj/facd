"""Verification report service orchestrating assembly, QR code, digital signing, and archival."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import Settings
from app.models.report import VerificationReportModel
from app.modules.report_generator.assembler import ReportAssembler
from app.modules.report_generator.json_renderer import export_json_report
from app.modules.report_generator.pdf_renderer import PDFReportRenderer
from app.modules.report_generator.qr_generator import generate_report_qr
from app.modules.report_generator.signer import sign_report, verify_report_signature
from app.schemas.decision import FinalVerificationDecision
from app.schemas.explainability import ExplainabilityReport
from app.schemas.pipeline import CertificateFields
from app.schemas.report import (
    FileMetadata,
    FullVerificationReport,
    SubsystemScoreItem,
    VisualEvidencePaths,
)


class ReportService:
    """Production service for generating, signing, rendering, and retrieving
    verification reports.
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        settings = Settings()
        self.output_dir = Path(output_dir or settings.REPORT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.secret_key = secret_key or settings.SECRET_KEY
        self.base_url = base_url or f"http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}"

    def generate_report(
        self,
        certificate_id: str,
        decision: FinalVerificationDecision,
        file_metadata: Optional[FileMetadata] = None,
        extracted_fields: Optional[CertificateFields] = None,
        explainability_report: Optional[ExplainabilityReport] = None,
        visual_evidence: Optional[VisualEvidencePaths] = None,
        subsystem_scores: Optional[List[SubsystemScoreItem]] = None,
        report_id: Optional[str] = None,
        verifier_username: str = "System Autopilot",
        db: Optional[Session] = None,
    ) -> FullVerificationReport:
        """Generate, digitally sign, render PDF and JSON, and archive report dossier.

        Args:
            certificate_id: Unique certificate ID.
            decision: Multimodal score fusion decision.
            file_metadata: Optional certificate file metadata.
            extracted_fields: Optional OCR-extracted academic credentials.
            explainability_report: Optional SHAP & overlay explainability output.
            visual_evidence: Optional paths to visual evidence plates.
            subsystem_scores: Optional explicit subsystem score list.
            report_id: Optional predetermined report ID.
            verifier_username: Operator/auditor identity.
            db: Optional SQLAlchemy session for database persistence.

        Returns:
            Populated, signed, and persisted FullVerificationReport.
        """
        # 1. Assemble Data Model
        report = ReportAssembler.assemble(
            certificate_id=certificate_id,
            decision=decision,
            file_metadata=file_metadata,
            extracted_fields=extracted_fields,
            explainability_report=explainability_report,
            visual_evidence=visual_evidence,
            subsystem_scores=subsystem_scores,
            report_id=report_id,
            verifier_username=verifier_username,
            base_url=self.base_url,
        )

        # 2. Generate Scannable QR Code
        qr_path = generate_report_qr(
            report_id=report.report_id,
            base_url=self.base_url,
            output_dir=self.output_dir,
        )
        report.qr_code_path = str(qr_path)

        # 3. Compute Tamper-Evident HMAC-SHA256 Signature
        signature = sign_report(report, self.secret_key)
        report.report_hmac_signature = signature

        # 4. Render Multi-page PDF Report
        pdf_path = self.output_dir / f"{report.report_id}.pdf"
        PDFReportRenderer.render(report, pdf_path)
        report.pdf_path = str(pdf_path)

        # 5. Export Standard JSON Report
        json_path = self.output_dir / f"{report.report_id}.json"
        export_json_report(report, json_path)
        report.json_path = str(json_path)

        # 6. Database Persistence (if db session provided)
        if db is not None:
            self._persist_to_db(report, db)

        return report

    def get_report(
        self,
        report_id: str,
        db: Optional[Session] = None,
    ) -> Optional[FullVerificationReport]:
        """Retrieve archived report by ID from filesystem or database."""
        json_file = self.output_dir / f"{report_id}.json"
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return FullVerificationReport.model_validate(data)
            except Exception as e:
                logger.error("Failed to parse json file for report %s: %s", report_id, e)

        # Fallback to DB
        if db is not None:
            record = db.query(VerificationReportModel).filter_by(id=report_id).first()
            if record and record.report_data_json:
                try:
                    return FullVerificationReport.model_validate(record.report_data_json)
                except Exception as e:
                    logger.error(
                        "Failed to validate report_data_json from DB for %s: %s", report_id, e
                    )

        return None

    def get_pdf_path(self, report_id: str) -> Optional[Path]:
        """Return path to compiled PDF report if it exists."""
        pdf_file = self.output_dir / f"{report_id}.pdf"
        if pdf_file.exists() and pdf_file.is_file():
            return pdf_file
        return None

    def verify_authenticity(self, report: FullVerificationReport) -> bool:
        """Verify whether report contents match the cryptographic digital signature."""
        if not report.report_hmac_signature:
            return False
        return verify_report_signature(report, report.report_hmac_signature, self.secret_key)

    def _persist_to_db(self, report: FullVerificationReport, db: Session) -> None:
        """Upsert report metadata into verification_reports table."""
        try:
            record = (
                db.query(VerificationReportModel)
                .filter(
                    (VerificationReportModel.id == report.report_id)
                    | (VerificationReportModel.certificate_id == report.certificate_id)
                )
                .first()
            )
            if record is None:
                record = VerificationReportModel(
                    id=report.report_id,
                    certificate_id=report.certificate_id,
                    overall_score=report.authenticity_score,
                    risk_score=report.risk_score,
                    verdict=report.verdict.value,
                    confidence_score=report.confidence_score,
                    sub_scores_json=[s.model_dump() for s in report.subsystem_scores],
                    veto_applied=report.veto_applied,
                    veto_reason=report.veto_reason,
                    contributing_factors_json=[f.model_dump() for f in report.findings],
                    execution_time_ms=0.0,
                    pdf_path=report.pdf_path,
                    json_path=report.json_path,
                    qr_path=report.qr_code_path,
                    hmac_signature=report.report_hmac_signature,
                    report_data_json=report.model_dump(mode="json"),
                )
                db.add(record)
            else:
                record.id = report.report_id
                record.overall_score = report.authenticity_score
                record.risk_score = report.risk_score
                record.verdict = report.verdict.value
                record.confidence_score = report.confidence_score
                record.sub_scores_json = [s.model_dump() for s in report.subsystem_scores]
                record.contributing_factors_json = [f.model_dump() for f in report.findings]
                record.pdf_path = report.pdf_path
                record.json_path = report.json_path
                record.qr_path = report.qr_code_path
                record.hmac_signature = report.report_hmac_signature
                record.report_data_json = report.model_dump(mode="json")
            db.commit()
        except Exception as exc:
            logger.exception("Failed to persist report to database: %s", exc)
            db.rollback()
