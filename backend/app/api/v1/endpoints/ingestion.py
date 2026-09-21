import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.modules.ingestion.service import DocumentIngestionService, get_ingestion_service
from app.schemas.ingestion import IngestedDocumentResponse

router = APIRouter(tags=["Documents"])


@router.post(
    "/documents/upload",
    response_model=IngestedDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload certificate document for verification",
    description=(
        "Accepts JPG, PNG, or PDF certificate files up to 10MB. "
        "Validates format via magic bytes, enforces resolution, "
        "computes cryptographic SHA-256 fingerprint, "
        "extracts forensic metadata, and rasterizes PDFs."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="Certificate image or PDF file"),
    template_id: Optional[str] = Form(None, description="Optional registered template ID"),
    service: DocumentIngestionService = Depends(get_ingestion_service),
) -> IngestedDocumentResponse:
    """Handle multipart file upload, validate integrity, and store for verification pipeline."""
    original_filename = file.filename or "document.bin"
    job_id = str(uuid.uuid4())

    ingested = service.ingest(
        file_stream=file.file,
        original_filename=original_filename,
    )

    return IngestedDocumentResponse(
        document_id=str(ingested.certificate_id),
        job_id=job_id,
        status="QUEUED",
        created_at=ingested.created_at,
        original_filename=ingested.metadata.original_filename,
        mime_type=ingested.metadata.mime_type,
        file_size_bytes=ingested.metadata.file_size_bytes,
        sha256_checksum=ingested.metadata.sha256_checksum,
        is_pdf=ingested.is_pdf,
        page_count=ingested.page_count,
        image_width=ingested.metadata.image_width,
        image_height=ingested.metadata.image_height,
        suspicious_indicators=ingested.metadata.suspicious_indicators,
    )
