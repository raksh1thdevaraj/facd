"""Sequential verification pipeline orchestrator executing 10 analytical stages
with graceful degradation.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.config import settings
from app.models.certificate import CertificateModel
from app.models.forensic import ForensicFindingModel
from app.models.ocr_field import OCRFieldModel
from app.models.text_consistency import TextConsistencyModel
from app.modules.explainability.service import ExplainabilityService
from app.modules.forensics.service import ForensicService
from app.modules.ingestion.rasterizer import PDFRasterizer
from app.modules.ml_classifier.service import BaselineMLService
from app.modules.ocr.service import OCRService
from app.modules.preprocessing.service import PreprocessingService
from app.modules.report_generator.service import ReportService
from app.modules.score_fusion.service import ScoreFusionService
from app.modules.template_matching.service import TemplateVerificationService
from app.modules.text_consistency.service import TextConsistencyService
from app.modules.visual_model.service import VisualCNNService
from app.schemas.explainability import FindingBullet, FindingCategory, FindingSeverity
from app.schemas.pipeline import CertificateFields
from app.schemas.report import FileMetadata, FullVerificationReport
from app.services.audit_service import AuditService
from app.services.fallback_handler import FallbackHandler, run_with_timeout
from app.services.pipeline_context import PipelineExecutionContext

logger = logging.getLogger(__name__)


class VerificationPipelineOrchestrator:
    """Orchestrates end-to-end multi-stage certificate verification with stage timeout isolation."""

    def __init__(self) -> None:
        self.preprocessing_service = PreprocessingService()
        self.ocr_service = OCRService()
        self.text_service = TextConsistencyService()
        self.forensic_service = ForensicService()
        self.template_service = TemplateVerificationService()
        self.ml_service = BaselineMLService()
        self.visual_service = VisualCNNService()
        self.score_fusion_service = ScoreFusionService()
        self.explainability_service = ExplainabilityService()
        self.report_service = ReportService()

    def execute_stage(
        self,
        stage_name: str,
        timeout_seconds: float,
        stage_fn: Callable[[], Any],
        context: PipelineExecutionContext,
    ) -> Any:
        """Execute a stage with timeout guard and fallback recovery."""
        start_time = time.perf_counter()
        try:
            result = run_with_timeout(stage_fn, timeout_seconds)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            context.stage_timings_ms[stage_name] = round(elapsed_ms, 2)
            return result
        except TimeoutError as te:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            context.stage_timings_ms[stage_name] = round(elapsed_ms, 2)
            logger.warning(
                "Stage '%s' timed out (%.1f ms). Applying fallback.", stage_name, elapsed_ms
            )
            return FallbackHandler.get_fallback_result(stage_name, context, str(te))
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            context.stage_timings_ms[stage_name] = round(elapsed_ms, 2)
            logger.warning("Stage '%s' failed (%s). Applying fallback.", stage_name, exc)
            return FallbackHandler.get_fallback_result(stage_name, context, str(exc))

    def run_pipeline(self, certificate_id: str, db: Session) -> FullVerificationReport:
        """Execute all pipeline analysis stages sequentially and update database progress."""
        cert = db.query(CertificateModel).filter_by(id=certificate_id).first()
        if cert is None:
            raise ValueError(f"Certificate record '{certificate_id}' not found.")

        file_path = Path(str(cert.file_path))
        context = PipelineExecutionContext(
            certificate_id=certificate_id,
            raw_image_path=file_path,
        )

        try:
            # Stage 1: Ingestion & Input Verification
            cert.job_status = "PROCESSING"
            cert.job_progress = 10
            cert.job_error = None
            db.commit()

            if not file_path.exists():
                raise FileNotFoundError(f"Certificate image file missing at {file_path}")

            # Check if PDF input requires rasterization to PNG
            if file_path.suffix.lower() == ".pdf":
                raster_dir = settings.UPLOAD_DIR / "rasterized"
                raster_dir.mkdir(parents=True, exist_ok=True)
                pages = PDFRasterizer.rasterize_pdf(
                    file_path, output_dir=raster_dir, dpi=300, max_pages=1
                )
                if pages:
                    context.raw_image_path = pages[0]

            # Read image array into memory bus
            img_bgr = cv2.imread(str(context.raw_image_path or file_path))
            if img_bgr is None:
                img_bgr = np.zeros((1000, 700, 3), dtype=np.uint8)
            context.raw_image = img_bgr

            cert.job_progress = 20
            db.commit()

            # Stage 2: Image Preprocessing (Deskew, CLAHE, Binarization)
            def _run_preprocessing() -> Any:
                try:
                    doc_uuid = uuid.UUID(certificate_id)
                except ValueError:
                    doc_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, certificate_id)
                return self.preprocessing_service.preprocess(doc_uuid, context.raw_image_path or file_path)

            prep_res = self.execute_stage("preprocessing", 10.0, _run_preprocessing, context)
            if hasattr(prep_res, "enhanced_image") and prep_res.enhanced_image is not None:
                context.enhanced_image = prep_res.enhanced_image
                context.binarized_image = prep_res.binarized_image
            else:
                context.enhanced_image = img_bgr
                context.binarized_image = img_bgr

            cert.job_progress = 30
            db.commit()

            # Stage 3: OCR & Credential Field Extraction
            def _run_ocr() -> Any:
                ocr_img = context.enhanced_image if context.enhanced_image is not None else img_bgr
                return self.ocr_service.process_document(certificate_id, ocr_img)

            ocr_res = self.execute_stage("ocr", 20.0, _run_ocr, context)
            context.ocr_result = ocr_res
            context.ocr_fields = ocr_res.fields if ocr_res else CertificateFields()
            context.ocr_tokens = getattr(self.ocr_service, "last_tokens", [])

            # Persist extracted OCR fields to database
            added_any = False
            if context.ocr_fields:
                field_names = [
                    "student_name",
                    "register_number",
                    "institution_name",
                    "course_degree",
                    "grade_or_marks",
                    "issue_date",
                    "certificate_number",
                ]
                for fn in field_names:
                    val = getattr(context.ocr_fields, fn, None)
                    if val:
                        db.add(
                            OCRFieldModel(
                                certificate_id=certificate_id,
                                field_name=fn,
                                field_value=str(val),
                                confidence_score=0.92,
                                is_flagged=False,
                            )
                        )
                        added_any = True

            if not added_any:
                raw_text = (
                    getattr(context.ocr_result, "raw_extracted_text", "")
                    if context.ocr_result
                    else ""
                )
                conf = (
                    getattr(context.ocr_result, "average_ocr_confidence", 0.0)
                    if context.ocr_result
                    else 0.0
                )
                db.add(
                    OCRFieldModel(
                        certificate_id=certificate_id,
                        field_name="raw_text",
                        field_value=raw_text or "unextracted",
                        confidence_score=conf or 0.0,
                        is_flagged=False,
                    )
                )

            cert.job_progress = 45
            db.commit()

            # Stage 4: Text Consistency Analysis
            def _run_text() -> Any:
                return self.text_service.analyze(
                    document_id=certificate_id,
                    ocr_tokens=context.ocr_tokens,
                    image_or_path=context.enhanced_image,
                    extracted_fields=context.ocr_fields,
                )

            text_res = self.execute_stage("text_consistency", 8.0, _run_text, context)
            context.text_result = text_res
            if text_res:
                db.add(
                    TextConsistencyModel(
                        certificate_id=certificate_id,
                        overall_score=text_res.overall_text_consistency_score,
                        baseline_score=text_res.baseline_alignment_score,
                        font_size_score=text_res.font_size_consistency_score,
                        stroke_weight_score=text_res.stroke_weight_consistency_score,
                        spacing_score=text_res.spacing_consistency_score,
                        logical_score=text_res.logical_consistency_score,
                        anomalous_regions_json=[r.model_dump() for r in text_res.anomalous_regions],
                    )
                )

            cert.job_progress = 55
            db.commit()

            # Stage 5: Image Forensics (ELA & Copy-Move)
            def _run_forensics() -> Any:
                raw_img = context.raw_image if context.raw_image is not None else img_bgr
                return self.forensic_service.analyze(
                    document_id=certificate_id,
                    raw_image_or_path=raw_img,
                )

            forensic_res = self.execute_stage("forensics", 10.0, _run_forensics, context)
            context.forensic_result = forensic_res
            if forensic_res:
                db.add(
                    ForensicFindingModel(
                        certificate_id=certificate_id,
                        finding_type="ELA_CONSISTENCY",
                        confidence_score=forensic_res.overall_forensic_score,
                        description=(
                            f"Forensic authenticity score: "
                            f"{forensic_res.overall_forensic_score:.2f}"
                        ),
                    )
                )

            cert.job_progress = 65
            db.commit()

            # Stage 6: Institutional Template Alignment & Record Matching
            def _run_template() -> Any:
                tmpl_img = context.enhanced_image if context.enhanced_image is not None else img_bgr
                tmpl_fields = context.ocr_fields or CertificateFields()
                f_score = (
                    context.forensic_result.overall_forensic_score
                    if context.forensic_result
                    else 1.0
                )
                t_score = (
                    context.text_result.overall_text_consistency_score
                    if context.text_result
                    else 1.0
                )
                return self.template_service.verify(
                    query_img=tmpl_img,
                    extracted_fields=tmpl_fields,
                    db=db,
                    document_id=certificate_id,
                    certificate_id=certificate_id,
                    forensic_score=f_score,
                    text_score=t_score,
                    save_to_db=True,
                )

            tmpl_res = self.execute_stage("template_matching", 8.0, _run_template, context)
            context.template_result = tmpl_res
            if tmpl_res and hasattr(tmpl_res, "tier_classification"):
                context.tier_result = tmpl_res.tier_classification.tier.value
            else:
                context.tier_result = "TIER_3_UNVERIFIED"

            cert.job_progress = 75
            db.commit()

            # Stage 7: ML Baseline & Visual Deep CNN Inference
            def _run_ml() -> Any:
                return self.ml_service.classify_certificate(
                    certificate_id=certificate_id,
                    ocr_result=context.ocr_result,
                    text_consistency_result=context.text_result,
                    forensics_result=context.forensic_result,
                    template_result=context.template_result,
                    db_session=db,
                )

            ml_res = self.execute_stage("ml_classifier", 6.0, _run_ml, context)
            context.tabular_prediction = ml_res

            def _run_visual() -> Any:
                vis_path = context.raw_image_path or file_path
                return self.visual_service.predict(
                    image_path=vis_path,
                    certificate_id=certificate_id,
                    db_session=db,
                )

            visual_res = self.execute_stage("visual_model", 8.0, _run_visual, context)
            context.visual_prediction = visual_res

            cert.job_progress = 85
            db.commit()

            # Stage 8: Multimodal Score Fusion & Verdict Engine
            def _run_fusion() -> Any:
                vis_prob = (
                    context.visual_prediction.manipulation_probability
                    if context.visual_prediction
                    else 0.10
                )
                tab_prob = (
                    context.tabular_prediction.manipulation_probability
                    if context.tabular_prediction
                    else 0.10
                )
                f_score = (
                    context.forensic_result.overall_forensic_score
                    if context.forensic_result
                    else 0.90
                )
                t_score = (
                    context.text_result.overall_text_consistency_score
                    if context.text_result
                    else 0.90
                )
                tmpl_score = 0.85
                if (
                    context.template_result
                    and hasattr(context.template_result, "template_metrics")
                    and context.template_result.template_metrics
                ):
                    tmpl_score = context.template_result.template_metrics.overall_template_score

                return self.score_fusion_service.fuse_and_decide(
                    certificate_id=certificate_id,
                    visual_fake_prob=vis_prob,
                    tabular_fake_prob=tab_prob,
                    forensic_score=f_score,
                    text_consistency_score=t_score,
                    template_score=tmpl_score,
                    tier_status=context.tier_result or "TIER_3_UNVERIFIED",
                    db_session=None,
                )

            decision = self.execute_stage("score_fusion", 4.0, _run_fusion, context)
            if context.warnings and decision:
                if hasattr(decision, "summary_rationale"):
                    decision.summary_rationale += " Notice: " + " ".join(context.warnings)
            context.final_decision = decision

            cert.job_progress = 90
            db.commit()

            # Stage 9: Explainability & Unified Overlays
            def _run_explain() -> Any:
                tabular_vec = np.zeros((1, 26), dtype=np.float32)
                exp_path = context.raw_image_path or file_path
                exp_decision = context.final_decision or decision
                return self.explainability_service.explain_certificate(
                    certificate_id=certificate_id,
                    raw_image_path=exp_path,
                    decision=exp_decision,
                    tabular_features=tabular_vec,
                )

            explainability_report = self.execute_stage("explainability", 8.0, _run_explain, context)
            if context.warnings and explainability_report:
                for w in context.warnings:
                    bullet = FindingBullet(
                        id=f"WARN_{uuid.uuid4().hex[:6]}",
                        severity=FindingSeverity.WARNING,
                        category=FindingCategory.TEMPLATE_MATCH,
                        title="Pipeline Stage Fallback Advisory",
                        description=f"Fallback advisory notice: {w}",
                    )
                    if hasattr(explainability_report, "key_findings"):
                        explainability_report.key_findings.append(bullet)
                    if hasattr(explainability_report, "primary_verdict_rationale"):
                        explainability_report.primary_verdict_rationale += " Notice: " + " ".join(
                            context.warnings
                        )
            context.explainability_report = explainability_report

            cert.job_progress = 95
            db.commit()

            # Stage 10: Official Verification Report Generation & Archival
            cert_file_size = getattr(cert, "file_size", 0)
            file_meta = FileMetadata(
                filename=str(cert.original_filename),
                file_size_kb=round(float(cert_file_size) / 1024.0, 1),
                file_format=str(cert.mime_type).split("/")[-1].upper(),
                sha256_checksum=str(cert.file_hash),
            )

            full_report = self.report_service.generate_report(
                certificate_id=certificate_id,
                decision=context.final_decision or decision,
                file_metadata=file_meta,
                extracted_fields=context.ocr_fields or CertificateFields(),
                explainability_report=context.explainability_report,
                db=db,
            )
            context.final_report = full_report

            # Mark Certificate as Completed
            cert.job_status = "COMPLETED"
            cert.job_progress = 100
            cert.job_error = None
            db.commit()

            AuditService.log_action(
                db=db,
                action="VERIFICATION_COMPLETED",
                certificate_id=certificate_id,
                details={
                    "verdict": full_report.verdict.value,
                    "authenticity_score": full_report.authenticity_score,
                    "report_id": full_report.report_id,
                    "stage_timings_ms": context.stage_timings_ms,
                },
            )

            # Persist to unified Verification History store (SQLite + data/history.json)
            try:
                from app.services.history_service import history_service

                student_name = "Not Detected"
                identifier = "Not Detected"
                institution = "Visvesvaraya Technological University"
                if context.ocr_fields:
                    student_name = getattr(context.ocr_fields, "student_name", None) or "Not Detected"
                    identifier = getattr(context.ocr_fields, "usn", None) or getattr(context.ocr_fields, "reg_no", None) or "Not Detected"
                    institution = getattr(context.ocr_fields, "institution_name", None) or institution

                t_flags = []
                report_flags = getattr(full_report, "tampering_flags", None)
                if report_flags:
                    t_flags = list(report_flags)
                elif context.warnings:
                    t_flags = list(context.warnings)

                qr_detected = bool(
                    context.template_result
                    and getattr(context.template_result, "qr_payload", None)
                )

                history_service.record_verification_async(
                    record_id=certificate_id,
                    timestamp_iso=datetime.now(timezone.utc).isoformat(),
                    original_filename=str(cert.original_filename),
                    document_type="VTU_MARKSCARD",
                    student_name=student_name,
                    identifier=identifier,
                    issuer=institution,
                    verdict=full_report.verdict.value,
                    confidence_score=float(full_report.authenticity_score),
                    qr_status=qr_detected,
                    tampering_flags=t_flags,
                    remarks=getattr(full_report, "notes", "") or f"Automated audit verdict: {full_report.verdict.value}",
                    full_details=full_report.model_dump() if hasattr(full_report, "model_dump") else {},
                )
            except Exception as hist_err:
                logger.warning("Could not record verification history for %s: %s", certificate_id, hist_err)

            return full_report

        except Exception as exc:
            db.rollback()
            logger.error("Pipeline failed for certificate %s: %s", certificate_id, exc)
            try:
                failed_cert = db.query(CertificateModel).filter_by(id=certificate_id).first()
                if failed_cert:
                    failed_cert.job_status = "FAILED"
                    failed_cert.job_error = str(exc)
                    db.commit()
            except Exception:
                pass

            AuditService.log_action(
                db=db,
                action="VERIFICATION_FAILED",
                certificate_id=certificate_id,
                details={"error": str(exc)},
            )
            raise
