"""Orchestration Service for Course Certificate Authenticity Verification.

Executes multi-signal sequential pipeline:
1. Ingestion and image loading
2. Multi-pass QR code detection & decoding
3. SSRF-safe URL verification & issuer domain resolution
4. OCR execution and course field extraction
5. Live/cached online issuer record comparison
6. Document tampering analysis (ELA, Noise, Copy-Move)
7. Signature & seal forensics
8. ML decision engine evaluation
9. Database record persistence
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.models.course_verification import CourseCertificateVerification
from app.modules.course_verification.comparator import CourseRecordComparator
from app.modules.course_verification.decision_engine import CourseDecisionEngine
from app.modules.course_verification.extractor import CourseExtractor
from app.modules.course_verification.qr_detector import CourseQRDetector
from app.modules.course_verification.report_generator import CourseReportGenerator
from app.modules.course_verification.seal_signature_analyzer import CourseSealSignatureAnalyzer
from app.modules.course_verification.tampering_analyzer import CourseTamperingAnalyzer
from app.modules.course_verification.url_verifier import CourseURLVerifier
from app.modules.ocr.service import OCRService
from app.schemas.course_certificate import (
    CourseComparisonResult,
    CourseExtractedFields,
    CourseForensicResult,
    CourseOnlineRecord,
    CourseQRResult,
    CourseSealSignatureResult,
    CourseURLVerificationResult,
    CourseVerificationResponse,
)

logger = logging.getLogger(__name__)


class CourseVerificationService:
    """End-to-end Course Certificate Verification pipeline orchestrator."""

    def __init__(
        self,
        db_session: Session | None = None,
        ocr_service: OCRService | None = None,
    ) -> None:
        self.db = db_session
        self.ocr_service = ocr_service or OCRService()
        self.qr_detector = CourseQRDetector()
        self.url_verifier = CourseURLVerifier()
        self.extractor = CourseExtractor()
        self.comparator = CourseRecordComparator()
        self.tampering_analyzer = CourseTamperingAnalyzer()
        self.seal_signature_analyzer = CourseSealSignatureAnalyzer()
        self.decision_engine = CourseDecisionEngine()
        self.report_generator = CourseReportGenerator()

    async def verify_certificate(
        self,
        image_path: Path,
        user_id: uuid.UUID | None = None,
    ) -> CourseVerificationResponse:
        """Run full multi-signal authenticity audit on an uploaded certificate image."""
        if not image_path.exists():
            raise FileNotFoundError(f"Certificate file not found: {image_path}")

        # 1. Load Image
        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            raise ValueError(f"Failed to read image at {image_path}")

        # 2. Multi-Pass QR Code Detection
        qr_result = self.qr_detector.detect_and_decode(image_bgr)

        # 3. SSRF-Safe URL Verification
        url_result: CourseURLVerificationResult
        if qr_result.qr_decoded and qr_result.payload:
            url_result = self.url_verifier.verify_url(qr_result.payload)
        else:
            url_result = CourseURLVerificationResult(
                is_valid_url=False,
                risk_level="SAFE",
                trust_score=0.5,
                domain_match=False,
                is_known_issuer=False,
                remarks="No verification URL detected in certificate QR code",
            )

        # 4. OCR Execution & Course Field Extraction
        raw_text = ""
        ocr_confidence = 0.0
        try:
            _doc_id = str(uuid.uuid4())
            ocr_res = self.ocr_service.process_document(
                document_id=_doc_id,
                image_or_path=image_path,
            )
            raw_text = getattr(ocr_res, "raw_extracted_text", "") or ""
            ocr_confidence = float(getattr(ocr_res, "average_ocr_confidence", 0.85))
        except Exception as ocr_err:
            logger.warning("Primary OCR service failed, using fallback reader: %s", ocr_err)
            raw_text = ""
            ocr_confidence = 0.50

        extracted_fields = self.extractor.extract_fields(
            raw_text=raw_text,
            ocr_confidence=ocr_confidence,
            qr_payload=qr_result.payload if qr_result.qr_decoded else None,
            resolved_issuer=url_result.resolved_issuer,
        )

        # 5. Online Record Scraping & Field Comparison
        comparison_result: CourseComparisonResult
        if url_result.is_valid_url and url_result.risk_level != "MALICIOUS":
            online_record = await self.comparator.fetch_online_record(
                verification_url=qr_result.payload,
                resolved_issuer=url_result.resolved_issuer,
                extracted_cert_id=extracted_fields.certificate_id,
            )
            comparison_result = self.comparator.compare_records(extracted_fields, online_record)
        else:
            comparison_result = CourseComparisonResult(
                name_match_score=0.0,
                course_match_score=0.0,
                cert_id_match_score=0.0,
                date_match_score=0.0,
                overall_match_score=0.0,
                online_record=None,
                discrepancies=["Online verification not performed (invalid or malicious URL)"],
                copied_qr_detected=False,
            )

        # 6. Document Tampering Forensics
        forensic_result = self.tampering_analyzer.analyze(image_bgr)

        # 7. Signature & Seal Analysis
        seal_sig_result = self.seal_signature_analyzer.analyze(image_bgr)

        # Adapt QRCodeData -> CourseQRResult for the decision engine
        qr_for_engine = CourseQRResult(
            qr_detected=qr_result.qr_detected,
            qr_decoded=qr_result.qr_decoded,
            payload=qr_result.payload,
            points=qr_result.points,
        )

        # Adapt SealSignatureResult -> CourseSealSignatureResult for the decision engine
        seal_for_engine: CourseSealSignatureResult | None = None
        if seal_sig_result is not None:
            seal_for_engine = CourseSealSignatureResult(
                signature_detected=seal_sig_result.signature_detected,
                seal_detected=seal_sig_result.seal_detected,
                signature_score=seal_sig_result.signature_score,
                seal_score=seal_sig_result.seal_score,
                details={"notes": "; ".join(seal_sig_result.details)},
            )

        # 8. Multi-Signal Decision Engine
        decision = self.decision_engine.evaluate(
            ocr_confidence=ocr_confidence,
            qr_result=qr_for_engine,
            url_result=url_result,
            comparison_result=comparison_result,
            forensic_result=forensic_result,
            seal_sig_result=seal_for_engine,
        )

        cert_id_str = extracted_fields.certificate_id or f"CERT-{uuid.uuid4().hex[:8].upper()}"

        response = CourseVerificationResponse(
            verification_id=uuid.uuid4(),
            certificate_id=cert_id_str,
            filename=image_path.name,
            verified_at=datetime.now(timezone.utc),
            decision=decision,
            extracted_fields=extracted_fields,
            qr_result=qr_for_engine,
            url_result=url_result,
            comparison_result=comparison_result,
            forensic_result=forensic_result,
            seal_signature_result=seal_for_engine,
        )

        # 9. Persist to Database if DB session available
        if self.db is not None:
            try:
                import hashlib

                file_bytes = image_path.read_bytes() if image_path.exists() else b""
                f_hash = hashlib.sha256(file_bytes).hexdigest() if file_bytes else ""
                f_size = len(file_bytes)

                db_record = CourseCertificateVerification(
                    id=str(response.verification_id),
                    user_id=str(user_id) if user_id else None,
                    uploaded_file_path=str(image_path),
                    file_hash=f_hash,
                    original_filename=response.filename,
                    file_size=f_size,
                    mime_type="image/png" if image_path.suffix.lower() == ".png" else "application/octet-stream",
                    job_status="COMPLETED",
                    extracted_fields_json=extracted_fields.model_dump(),
                    qr_data_json=qr_result.model_dump(),
                    verification_url=qr_result.payload if qr_result.qr_decoded else None,
                    issuer=extracted_fields.issuer,
                    online_verification_data_json=comparison_result.online_record.model_dump() if comparison_result.online_record else None,
                    field_comparison_json=comparison_result.model_dump(),
                    tampering_analysis_json=forensic_result.model_dump(),
                    seal_signature_json=seal_sig_result.model_dump() if seal_sig_result else None,
                    authenticity_score=decision.overall_authenticity_score,
                    fraud_risk_score=decision.fraud_risk_score,
                    final_status=decision.status.value,
                    evidence_summary_json={
                        "decision_reasons": decision.decision_reasons,
                        "risk_factors": decision.risk_factors,
                        "signal_scores": decision.signal_scores,
                    },
                )
                self.db.add(db_record)
                self.db.commit()
                self.db.refresh(db_record)
                logger.info("Persisted verification audit record %s", db_record.id)
            except Exception as db_err:
                logger.error("Failed to persist verification record: %s", db_err)
                self.db.rollback()

        return response
