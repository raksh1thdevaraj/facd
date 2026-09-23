"""
Public Verification Hub Endpoint for Two-Role Certificate Authenticity Platform.
Supports frictionless verification for marks cards and course certificates.
"""

from __future__ import annotations

import os
import shutil
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.course_verification import CourseCertificateVerificationModel
from app.models.user import AppUserModel
from app.modules.ingestion.rasterizer import PDFRasterizer
from src.verify_certificate import get_certificate_verifier

router = APIRouter(prefix="/verify", tags=["Public Verification Hub"])

# In-memory fast cache for recent scans across sessions
RECENT_SCANS_CACHE: List[Dict[str, Any]] = []


def _save_scan_record(
    db: Session,
    scan_id: str,
    original_filename: str,
    certificate_type: str,
    result: Dict[str, Any],
    file_path: str,
    file_size: int,
    user_id: Optional[str] = None,
) -> None:
    """Persist verification scan result into database and in-memory cache."""
    now_iso = datetime.now(timezone.utc).isoformat()
    scan_entry = {
        "id": scan_id,
        "user_id": user_id,
        "filename": original_filename,
        "certificate_type": certificate_type,
        "final_status": result["final_status"],
        "verdict_badge": result["verdict_badge"],
        "color": result["color"],
        "is_authentic": result["is_authentic"],
        "confidence_score": result["confidence_score"],
        "latency_ms": result["latency_ms"],
        "rejection_reasons": result.get("rejection_reasons", []),
        "warnings": result.get("warnings", []),
        "forensic_cards": result.get("forensic_cards", {}),
        "timestamp": now_iso,
    }
    
    # Prepend to cache (keep last 100)
    RECENT_SCANS_CACHE.insert(0, scan_entry)
    if len(RECENT_SCANS_CACHE) > 100:
        RECENT_SCANS_CACHE.pop()

    # Save to database if available
    try:
        db_model = CourseCertificateVerificationModel(
            id=scan_id,
            user_id=user_id,
            uploaded_file_path=file_path,
            file_hash=uuid.uuid4().hex,
            original_filename=original_filename,
            file_size=file_size,
            mime_type="application/pdf" if original_filename.lower().endswith(".pdf") else "image/png",
            job_status="COMPLETED",
            final_status=result["final_status"],
            authenticity_score=result["confidence_score"],
            fraud_risk_score=round(1.0 - result["confidence_score"], 3),
            qr_data_json=result.get("forensic_cards", {}).get("qr_and_url"),
            tampering_analysis_json=result.get("forensic_cards", {}).get("layout_alignment"),
            seal_signature_json=result.get("forensic_cards", {}).get("template_integrity"),
            evidence_summary_json={
                "rejection_reasons": result.get("rejection_reasons", []),
                "warnings": result.get("warnings", []),
                "latency_ms": result["latency_ms"],
            }
        )
        db.add(db_model)
        db.commit()
    except Exception as exc:
        db.rollback()
        # Non-fatal logging if DB write encounters issues
        print(f"[!] Warning saving scan to DB: {exc}")


@router.post(
    "",
    summary="Verify an academic marks card or course completion certificate",
    response_model=Dict[str, Any],
)
async def verify_certificate(
    file: UploadFile = File(...),
    certificate_type: str = Form("marks_card"),
    expected_student_name: Optional[str] = Form(None),
    expected_reg_no: Optional[str] = Form(None),
    current_user: AppUserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Authenticated entrypoint for certificate forensic verification.
    Requires valid Bearer token from registered user or admin.
    Accepts: PDF, PNG, JPG, JPEG, TIFF.
    Executes:
    1. QR code and provider domain whitelist accreditation.
    2. OCR baseline horizontal alignment and spliced grade detection.
    3. DIAR-AI reference template integrity (SSIM >= 0.85 & Canny Edge Diff <= 0.08).
    4. Optional metadata cross-verification.
    """
    scan_id = str(uuid.uuid4())
    filename = file.filename or f"upload_{scan_id}.png"
    ext = Path(filename).suffix.lower()

    allowed_exts = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".pdf"}
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Supported formats: {', '.join(sorted(allowed_exts))}",
        )

    # Prepare temp directory
    upload_dir = Path("storage/uploads/verify")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_file_path = upload_dir / f"{scan_id}_{filename}"

    file_bytes = await file.read()
    with open(temp_file_path, "wb") as f:
        f.write(file_bytes)

    # Convert PDF to rasterized image if PDF
    img_bgr: Optional[np.ndarray] = None
    if ext == ".pdf":
        raster_dir = upload_dir / f"raster_{scan_id}"
        try:
            pages = PDFRasterizer.rasterize_pdf(temp_file_path, raster_dir, dpi=200, max_pages=1)
            if pages:
                img_bgr = cv2.imread(str(pages[0]))
        except Exception as e:
            # Fallback direct cv2 or raise
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unable to rasterize PDF certificate: {str(e)}",
            )
    else:
        # Decode image from bytes or file path
        nparr = np.frombuffer(file_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_bgr is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to decode image data from uploaded certificate.",
        )

    # Run verification pipeline
    verifier = get_certificate_verifier()
    result = verifier.verify(
        image_bgr=img_bgr,
        certificate_type=certificate_type,
        expected_student_name=expected_student_name,
        expected_reg_no=expected_reg_no,
    )

    # Add scan metadata
    result["scan_id"] = scan_id
    result["filename"] = filename
    result["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Save record
    _save_scan_record(
        db=db,
        scan_id=scan_id,
        original_filename=filename,
        certificate_type=certificate_type,
        result=result,
        file_path=str(temp_file_path),
        file_size=len(file_bytes),
        user_id=str(current_user.id) if current_user and current_user.id else None,
    )

    return result


@router.get(
    "/sample-data",
    summary="Get pre-configured demo test certificates and verification scenarios",
    response_model=List[Dict[str, Any]],
)
def get_sample_test_scenarios() -> List[Dict[str, Any]]:
    """
    Returns pre-loaded sample certificates to demonstrate:
    - Authentic university marks card
    - Spliced / tampered marks card
    - Authentic online course certificate (Coursera/edX)
    - Unaccredited domain / forged course certificate
    """
    return [
        {
            "id": "sample-auth-marks-card",
            "name": "Authentic University Marks Card",
            "type": "marks_card",
            "issuer": "Heritage Technical University",
            "expected_verdict": "VERIFIED",
            "description": "Standard university degree marks card with official seal, high SSIM alignment, and accredited QR payload.",
            "demo_student_name": "Aarav Sharma",
            "demo_reg_no": "HTU2022-CS-041",
            "sample_file_path": "datasets/synthetic_manipulated/genuine/GEN_00001.png",
        },
        {
            "id": "sample-tampered-marks-card",
            "name": "Manipulated Marks Card (Spliced CGPA)",
            "type": "marks_card",
            "issuer": "Heritage Technical University",
            "expected_verdict": "REJECTED",
            "description": "Marks card where grades were altered using image splicing, triggering baseline variance and structural delta flags.",
            "demo_student_name": "Aarav Sharma",
            "demo_reg_no": "HTU2022-CS-041",
            "sample_file_path": "datasets/synthetic_manipulated/manipulated/MAN_00001.png",
        },
        {
            "id": "sample-auth-course-cert",
            "name": "Authentic Deep Learning Specialization",
            "type": "course_certificate",
            "issuer": "Coursera / Stanford Online",
            "expected_verdict": "VERIFIED",
            "description": "Industry course certificate featuring authentic accredited URL on coursera.org domain and crisp typography.",
            "demo_student_name": "Priya Nair",
            "demo_reg_no": "CRS-DL-889102",
            "sample_file_path": "datasets/synthetic_manipulated/genuine/GEN_00002.png",
        },
        {
            "id": "sample-forged-course-cert",
            "name": "Unaccredited Phishing Certificate",
            "type": "course_certificate",
            "issuer": "FakeEd Academy (Phishing Root)",
            "expected_verdict": "REJECTED",
            "description": "Forged credential containing QR redirecting to malicious non-accredited domain and inconsistent fonts.",
            "demo_student_name": "Vikram Sen",
            "demo_reg_no": "FAKE-2026-99",
            "sample_file_path": "datasets/synthetic_manipulated/manipulated/MAN_00002.png",
        },
    ]


@router.get(
    "/{scan_id}",
    summary="Retrieve forensic result for a previously processed scan",
    response_model=Dict[str, Any],
)
def get_scan_result(
    scan_id: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve scan result by ID from in-memory cache or database."""
    for scan in RECENT_SCANS_CACHE:
        if scan["id"] == scan_id:
            return scan

    db_record = db.query(CourseCertificateVerificationModel).filter(
        CourseCertificateVerificationModel.id == scan_id
    ).first()
    if not db_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification scan with ID '{scan_id}' not found.",
        )

    return {
        "id": db_record.id,
        "filename": db_record.original_filename,
        "certificate_type": "course_certificate",
        "final_status": db_record.final_status,
        "verdict_badge": db_record.final_status,
        "color": "emerald" if db_record.final_status == "VERIFIED" else "red",
        "is_authentic": db_record.final_status == "VERIFIED",
        "confidence_score": db_record.authenticity_score,
        "latency_ms": 120.0,
        "forensic_cards": {
            "qr_and_url": db_record.qr_data_json or {},
            "layout_alignment": db_record.tampering_analysis_json or {},
            "template_integrity": db_record.seal_signature_json or {},
        },
        "rejection_reasons": (db_record.evidence_summary_json or {}).get("rejection_reasons", []),
        "warnings": (db_record.evidence_summary_json or {}).get("warnings", []),
        "timestamp": db_record.created_at.isoformat() if hasattr(db_record, "created_at") and db_record.created_at else datetime.now(timezone.utc).isoformat(),
    }
