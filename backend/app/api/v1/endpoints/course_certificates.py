"""Course Certificate Authenticity Verification API Router.

Endpoints for uploading course certificates, multi-signal verification,
retrieving audit records, downloading PDF reports, and querying authoritative issuers.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.course_verification import CourseCertificateVerification
from app.models.issuer_registry import IssuerRegistry
from app.models.user import AppUserModel
from app.modules.course_verification.report_generator import CourseReportGenerator
from app.modules.course_verification.service import CourseVerificationService
from app.modules.course_verification.url_verifier import CourseURLVerifier
from app.schemas.course_certificate import (
    CourseURLVerificationResult,
    CourseVerificationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/course-certificates", tags=["Course Certificates"])


@router.post(
    "/verify",
    response_model=CourseVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload and verify a course certificate document",
    description=(
        "Performs complete multi-signal authenticity audit on an uploaded course certificate: "
        "QR code decoding, SSRF-safe URL verification, OCR field extraction, "
        "cross-modal comparison, pixel forensics (ELA, noise, copy-move), "
        "seal/signature analysis, and ML fraud risk scoring."
    ),
)
async def verify_course_certificate(
    file: UploadFile = File(
        ..., description="Course certificate image (PNG, JPG, JPEG) or document"
    ),
    current_user: AppUserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CourseVerificationResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file missing filename"
        )

    ext = Path(file.filename).suffix.lower()
    allowed_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".pdf"}
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {allowed_exts}",
        )

    # Save to temp uploads directory
    upload_dir = Path("uploads/course_certificates")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_filename = f"{uuid.uuid4()}{ext}"
    temp_path = upload_dir / temp_filename

    contents = await file.read()
    temp_path.write_bytes(contents)

    # If PDF, convert first page to image
    image_path_to_process = temp_path
    if ext == ".pdf":
        try:
            from app.modules.ingestion.rasterizer import PDFRasterizer

            pages = PDFRasterizer.rasterize_pdf(
                pdf_path=temp_path, output_dir=upload_dir, dpi=200, max_pages=1
            )
            if pages:
                image_path_to_process = pages[0]
        except Exception as pdf_err:
            logger.warning("Failed to rasterize PDF page: %s", pdf_err)

    service = CourseVerificationService(db_session=db)
    try:
        response = await service.verify_certificate(image_path=image_path_to_process)
        return response
    except Exception as exc:
        logger.exception("Error during course certificate verification: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {exc}",
        ) from exc


@router.get(
    "/{verification_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get course certificate verification audit record by ID",
)
def get_verification_record(
    verification_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    record = (
        db.query(CourseCertificateVerification)
        .filter(CourseCertificateVerification.id == str(verification_id))
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Verification record not found"
        )

    evidence = record.evidence_summary_json or {}
    return {
        "id": str(record.id),
        "certificate_id": (record.extracted_fields_json or {}).get("certificate_id"),
        "filename": record.original_filename,
        "status": record.final_status,
        "overall_authenticity_score": record.authenticity_score,
        "fraud_risk_score": record.fraud_risk_score,
        "decision_reasons": evidence.get("decision_reasons", []),
        "risk_factors": evidence.get("risk_factors", []),
        "signal_scores": evidence.get("signal_scores", {}),
        "extracted_fields": record.extracted_fields_json,
        "qr_result": record.qr_data_json,
        "url_result": record.field_comparison_json,
        "comparison_result": record.field_comparison_json,
        "forensic_result": record.tampering_analysis_json,
        "seal_signature_result": record.seal_signature_json,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.get(
    "/{verification_id}/report",
    status_code=status.HTTP_200_OK,
    summary="Download publication-grade PDF verification audit report",
)
def download_verification_report(
    verification_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    record = (
        db.query(CourseCertificateVerification)
        .filter(CourseCertificateVerification.id == str(verification_id))
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Verification record not found"
        )

    evidence = record.evidence_summary_json or {}
    extracted = record.extracted_fields_json or {}
    cert_id = extracted.get("certificate_id") or str(record.id)[:8]

    # Reconstitute CourseVerificationResponse
    response_obj = CourseVerificationResponse.model_validate(
        {
            "verification_id": record.id,
            "certificate_id": cert_id,
            "filename": record.original_filename,
            "verified_at": record.created_at,
            "decision": {
                "status": record.final_status,
                "overall_authenticity_score": record.authenticity_score,
                "fraud_risk_score": record.fraud_risk_score,
                "decision_reasons": evidence.get("decision_reasons", []),
                "risk_factors": evidence.get("risk_factors", []),
                "signal_scores": evidence.get("signal_scores", {}),
            },
            "extracted_fields": extracted,
            "qr_result": record.qr_data_json or {},
            "url_result": {
                "is_valid_url": bool(record.verification_url),
                "risk_level": "SAFE",
                "trust_score": 1.0,
                "domain_match": True,
                "is_known_issuer": bool(record.issuer),
            },
            "comparison_result": record.field_comparison_json
            or {
                "name_match_score": 1.0,
                "course_match_score": 1.0,
                "cert_id_match_score": 1.0,
                "date_match_score": 1.0,
                "overall_match_score": 1.0,
                "copied_qr_detected": False,
            },
            "forensic_result": record.tampering_analysis_json
            or {
                "tampering_detected": False,
                "tampering_probability": 0.0,
                "copy_move_detected": False,
                "noise_inconsistency_score": 0.0,
            },
            "seal_signature_result": record.seal_signature_json,
        }
    )

    report_gen = CourseReportGenerator()
    pdf_bytes = report_gen.generate_pdf(response_obj)

    filename = f"course_verification_report_{cert_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/issuers/list",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List authoritative course certificate issuers in registry",
)
def list_issuers(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    issuers = db.query(IssuerRegistry).order_by(IssuerRegistry.issuer_name.asc()).all()
    if not issuers:
        # Return default known issuers if DB empty
        from app.modules.course_verification.url_verifier import AUTHORITATIVE_ISSUERS

        return [
            {
                "name": name,
                "domain": info["primary_domain"],
                "is_active": True,
                "trust_score": 1.0,
            }
            for name, info in AUTHORITATIVE_ISSUERS.items()
        ]

    return [
        {
            "id": str(iss.id),
            "name": iss.issuer_name,
            "domain": iss.official_domain,
            "is_active": True,
            "trust_score": 1.0 if iss.trusted_status == "TRUSTED" else 0.5,
        }
        for iss in issuers
    ]


@router.get(
    "/{verification_id}/qr",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get extracted QR code payload and detection details for a verification",
)
def get_verification_qr(
    verification_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    record = (
        db.query(CourseCertificateVerification)
        .filter(CourseCertificateVerification.id == str(verification_id))
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Verification record not found"
        )
    return {
        "verification_id": str(record.id),
        "qr_data": record.qr_data_json or {},
        "verification_url": record.verification_url,
    }


@router.get(
    "/{verification_id}/online-verification",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get online registry verification record and cross-modal comparison",
)
def get_online_verification_data(
    verification_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    record = (
        db.query(CourseCertificateVerification)
        .filter(CourseCertificateVerification.id == str(verification_id))
        .first()
    )
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Verification record not found"
        )
    return {
        "verification_id": str(record.id),
        "issuer": record.issuer,
        "verification_url": record.verification_url,
        "online_verification_data": record.online_verification_data_json or {},
        "field_comparison": record.field_comparison_json or {},
    }


@router.post(
    "/issuers",
    response_model=dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new recognized course certificate credential issuer",
)
def register_issuer(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    issuer_name = payload.get("issuer_name", "").strip()
    official_domain = payload.get("official_domain", "").strip()
    verification_domain = payload.get("verification_domain", official_domain).strip()
    if not issuer_name or not official_domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="issuer_name and official_domain are required",
        )

    existing = db.query(IssuerRegistry).filter(IssuerRegistry.issuer_name == issuer_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Issuer already registered"
        )

    new_issuer = IssuerRegistry(
        issuer_name=issuer_name,
        official_domain=official_domain,
        verification_domain=verification_domain,
        verification_pattern=payload.get("verification_pattern"),
        certificate_id_pattern=payload.get("certificate_id_pattern"),
        trusted_status=payload.get("trusted_status", "TRUSTED"),
    )
    db.add(new_issuer)
    db.commit()
    db.refresh(new_issuer)
    return {
        "id": str(new_issuer.id),
        "issuer_name": new_issuer.issuer_name,
        "official_domain": new_issuer.official_domain,
        "trusted_status": new_issuer.trusted_status,
        "created_at": new_issuer.created_at.isoformat() if new_issuer.created_at else None,
    }


@router.post(
    "/verify-url",
    response_model=CourseURLVerificationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate verification URL and test issuer domain trust",
)
def verify_url_standalone(payload: dict[str, str]) -> CourseURLVerificationResult:
    url = payload.get("url", "").strip()
    if not url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL field is required")

    verifier = CourseURLVerifier()
    return verifier.verify_url(url)


# ==========================================
# Modular ML Service Endpoints (Requirement 22)
# ==========================================


@router.post(
    "/ml/ocr",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Direct ML OCR field extraction from uploaded certificate",
)
async def ml_extract_ocr(file: UploadFile = File(...)) -> dict[str, Any]:
    from app.modules.course_verification.extractor import CourseCertificateExtractor

    upload_dir = Path("uploads/temp_ml")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_file = upload_dir / f"{uuid.uuid4()}_{file.filename}"
    temp_file.write_bytes(await file.read())

    extractor = CourseCertificateExtractor()
    extracted = extractor.extract_from_image(temp_file)
    return {"extracted_fields": extracted.model_dump()}


@router.post(
    "/ml/qr",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Direct ML QR code detection and decoding from uploaded certificate",
)
async def ml_detect_qr(file: UploadFile = File(...)) -> dict[str, Any]:
    from app.modules.course_verification.qr_detector import CourseQRDetector

    upload_dir = Path("uploads/temp_ml")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_file = upload_dir / f"{uuid.uuid4()}_{file.filename}"
    temp_file.write_bytes(await file.read())

    detector = CourseQRDetector()
    qr_res = detector.detect_and_decode(temp_file)
    return {"qr_result": qr_res.model_dump()}


@router.post(
    "/ml/tampering",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Direct ML document tampering & pixel forensics analysis",
)
async def ml_analyze_tampering(file: UploadFile = File(...)) -> dict[str, Any]:
    from app.modules.course_verification.tampering_analyzer import CourseTamperingAnalyzer

    upload_dir = Path("uploads/temp_ml")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_file = upload_dir / f"{uuid.uuid4()}_{file.filename}"
    temp_file.write_bytes(await file.read())

    analyzer = CourseTamperingAnalyzer()
    tamper_res = analyzer.analyze_certificate(temp_file)
    return {"tampering_analysis": tamper_res.model_dump()}


@router.post(
    "/ml/score",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Direct ML fraud-risk and authenticity scoring from signal vector",
)
def ml_score_signals(payload: dict[str, Any]) -> dict[str, Any]:
    from app.modules.course_verification.decision_engine import CourseDecisionEngine
    from app.schemas.course_certificate import (
        CourseComparisonResult,
        CourseExtractedFields,
        CourseForensicResult,
        CourseQRResult,
        CourseURLVerificationResult,
    )

    engine = CourseDecisionEngine()
    extracted = CourseExtractedFields(**payload.get("extracted_fields", {}))
    qr_res = CourseQRResult(**payload.get("qr_result", {}))
    url_res = CourseURLVerificationResult(**payload.get("url_result", {}))
    comp_res = CourseComparisonResult(**payload.get("comparison_result", {}))
    forensic_res = CourseForensicResult(**payload.get("forensic_result", {}))

    ocr_conf = float(payload.get("ocr_confidence", extracted.ocr_confidence or 0.85))
    decision = engine.evaluate(
        ocr_confidence=ocr_conf,
        qr_result=qr_res,
        url_result=url_res,
        comparison_result=comp_res,
        forensic_result=forensic_res,
    )
    return {"decision": decision.model_dump()}
