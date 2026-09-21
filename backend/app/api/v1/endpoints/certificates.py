"""FastAPI router for certificate document upload, status polling, and verification history."""

from __future__ import annotations

import hashlib
import math
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.certificate import CertificateModel
from app.models.report import VerificationReportModel
from app.schemas.certificate import (
    CertificateDetailResponse,
    CertificateListItem,
    CertificatePaginatedList,
    CertificateStatusResponse,
    CertificateUploadResponse,
)
from app.schemas.decision import VerificationVerdict
from app.services.audit_service import AuditService
from app.services.task_runner import AsyncTaskRunner, get_task_runner

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.post(
    "/upload",
    response_model=CertificateUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload certificate document for asynchronous verification",
    description=(
        "Accepts PNG, JPG, or PDF files. Saves file, computes SHA-256 fingerprint, "
        "registers job as PENDING, and dispatches background analysis pipeline."
    ),
)
async def upload_certificate(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Certificate image or PDF document"),
    db: Session = Depends(get_db),
    task_runner: AsyncTaskRunner = Depends(get_task_runner),
) -> CertificateUploadResponse:
    cert_id = str(uuid.uuid4())
    filename = file.filename or "uploaded_certificate.png"

    # Read content and compute SHA-256
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    file_hash = hashlib.sha256(content).hexdigest()

    # Save to storage/uploads
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename).suffix or ".png"
    target_path = upload_dir / f"{cert_id}{suffix}"
    with open(target_path, "wb") as f:
        f.write(content)

    # Register in database
    cert = CertificateModel(
        id=cert_id,
        file_path=str(target_path),
        file_hash=file_hash,
        original_filename=filename,
        file_size=len(content),
        mime_type=file.content_type or "image/png",
        job_status="PENDING",
        job_progress=0,
    )
    db.add(cert)
    db.commit()
    db.refresh(cert)

    if settings.USE_FIRESTORE:
        from app.services.firestore_service import firestore_service
        firestore_service.save_certificate(
            cert_id,
            {
                "id": cert_id,
                "file_hash": file_hash,
                "original_filename": filename,
                "file_size": len(content),
                "mime_type": file.content_type or "image/png",
                "job_status": "PENDING",
                "job_progress": 0,
                "created_at": cert.created_at.isoformat() if cert.created_at else datetime.utcnow().isoformat(),
            },
        )

    # Record Audit Log
    client_ip = request.client.host if request.client else "127.0.0.1"
    AuditService.log_action(
        db=db,
        action="CERTIFICATE_UPLOADED",
        certificate_id=cert_id,
        ip_address=client_ip,
        details={"filename": filename, "file_size": len(content), "file_hash": file_hash},
    )

    # Dispatch Background Analysis
    task_runner.dispatch(certificate_id=cert_id, background_tasks=background_tasks)

    poll_url = f"/api/v1/certificates/{cert_id}/status"
    return CertificateUploadResponse(
        certificate_id=cert_id,
        status="PENDING",
        poll_url=poll_url,
        filename=filename,
        file_hash=file_hash,
        created_at=cert.created_at,
    )


@router.get(
    "/{certificate_id}/status",
    response_model=CertificateStatusResponse,
    summary="Poll verification job execution status and progress",
)
def get_certificate_status(
    certificate_id: str, db: Session = Depends(get_db)
) -> CertificateStatusResponse:
    cert = db.query(CertificateModel).filter_by(id=certificate_id).first()
    if cert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found.",
        )

    # Check if report ID exists
    rep = db.query(VerificationReportModel).filter_by(certificate_id=certificate_id).first()
    report_id = rep.id if rep else None

    return CertificateStatusResponse(
        id=cert.id,
        status=cert.job_status,
        progress=cert.job_progress,
        error=cert.job_error,
        report_id=report_id,
    )


@router.get(
    "/{certificate_id}",
    response_model=CertificateDetailResponse,
    summary="Get full certificate assessment details",
)
def get_certificate_details(
    certificate_id: str, db: Session = Depends(get_db)
) -> CertificateDetailResponse:
    cert = db.query(CertificateModel).filter_by(id=certificate_id).first()
    if cert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found.",
        )

    rep = db.query(VerificationReportModel).filter_by(certificate_id=certificate_id).first()

    return CertificateDetailResponse(
        id=cert.id,
        filename=cert.original_filename,
        file_hash=cert.file_hash,
        file_size=cert.file_size,
        mime_type=cert.mime_type,
        status=cert.job_status,
        progress=cert.job_progress,
        error=cert.job_error,
        created_at=cert.created_at,
        updated_at=cert.updated_at,
        preprocessed_image_path=cert.preprocessed_image_path,
        report_id=rep.id if rep else None,
        verdict=VerificationVerdict(rep.verdict) if rep and rep.verdict else None,
        authenticity_score=rep.overall_score if rep else None,
    )


@router.get(
    "",
    response_model=CertificatePaginatedList,
    summary="List certificate verification history with pagination",
)
def list_certificates(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    verdict: Optional[str] = Query(None, description="AUTHENTIC, SUSPICIOUS, MANIPULATED"),
    search: Optional[str] = Query(None, description="Search across filename or ID"),
    date_from: Optional[str] = Query(None, description="Filter records from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter records to date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> CertificatePaginatedList:
    query = db.query(CertificateModel)

    if status_filter:
        query = query.filter(CertificateModel.job_status == status_filter.upper())

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (CertificateModel.original_filename.ilike(search_pattern))
            | (CertificateModel.id.ilike(search_pattern))
        )

    if date_from:
        try:
            d_from = datetime.fromisoformat(date_from)
            query = query.filter(CertificateModel.created_at >= d_from)
        except Exception:
            pass

    if date_to:
        try:
            d_to = datetime.fromisoformat(date_to) + timedelta(days=1)
            query = query.filter(CertificateModel.created_at < d_to)
        except Exception:
            pass

    if verdict:
        query = query.join(
            VerificationReportModel,
            CertificateModel.id == VerificationReportModel.certificate_id,
        ).filter(VerificationReportModel.verdict == verdict.upper())

    total = query.count()
    offset = (page - 1) * limit
    certs = query.order_by(desc(CertificateModel.created_at)).offset(offset).limit(limit).all()

    items: list[CertificateListItem] = []
    for c in certs:
        rep = db.query(VerificationReportModel).filter_by(certificate_id=c.id).first()
        items.append(
            CertificateListItem(
                id=c.id,
                filename=c.original_filename,
                file_hash=c.file_hash,
                file_size=c.file_size,
                status=c.job_status,
                progress=c.job_progress,
                created_at=c.created_at,
                verdict=VerificationVerdict(rep.verdict) if rep and rep.verdict else None,
                authenticity_score=rep.overall_score if rep else None,
                report_id=rep.id if rep else None,
            )
        )

    total_pages = max(1, math.ceil(total / limit))
    return CertificatePaginatedList(
        items=items, total=total, page=page, limit=limit, total_pages=total_pages
    )


@router.delete(
    "/{certificate_id}",
    summary="Delete certificate and associated artifacts",
)
def delete_certificate(
    request: Request, certificate_id: str, db: Session = Depends(get_db)
) -> dict:
    cert = db.query(CertificateModel).filter_by(id=certificate_id).first()
    if cert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate '{certificate_id}' not found.",
        )

    # Remove file on disk if exists
    try:
        p = Path(cert.file_path)
        if p.exists():
            p.unlink()
    except Exception:
        pass

    db.delete(cert)
    db.commit()

    client_ip = request.client.host if request.client else "127.0.0.1"
    AuditService.log_action(
        db=db,
        action="CERTIFICATE_DELETED",
        certificate_id=certificate_id,
        ip_address=client_ip,
    )

    return {"deleted": True, "certificate_id": certificate_id}
