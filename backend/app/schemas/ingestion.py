from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pipeline import IngestionOutput


class IngestionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    QUEUED = "QUEUED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    CORRUPTED = "CORRUPTED"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"


class MetadataModel(BaseModel):
    """Extracted file and forensic metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_size_bytes: int = Field(..., ge=0, description="Size in bytes")
    mime_type: str = Field(..., description="Detected MIME type")
    original_filename: str = Field(..., description="Original client-supplied filename")
    sha256_checksum: str = Field(..., min_length=64, max_length=64, description="Hex digest")
    image_width: int = Field(..., ge=0, description="Width in pixels")
    image_height: int = Field(..., ge=0, description="Height in pixels")
    software_signature: Optional[str] = Field(
        default=None, description="Software tag found in EXIF or PDF metadata"
    )
    creation_date: Optional[datetime] = Field(
        default=None, description="Creation timestamp from metadata"
    )
    modification_date: Optional[datetime] = Field(
        default=None, description="Modification timestamp from metadata"
    )
    has_exif: bool = Field(default=False, description="True if EXIF tags were present")
    raw_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Raw dictionary of extracted tags"
    )
    suspicious_indicators: List[str] = Field(
        default_factory=list, description="Forensic metadata suspicion flags"
    )


class IngestedDocument(BaseModel):
    """Domain model representing a successfully ingested document ready for analysis."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    certificate_id: UUID = Field(..., description="Unique certificate identifier")
    original_file_path: Path = Field(..., description="Path to raw uploaded file on disk")
    working_image_path: Path = Field(
        ..., description="Path to rasterized or verified image on disk"
    )
    format: str = Field(..., description="Normalized file format (e.g. 'JPEG', 'PNG', 'PDF')")
    is_pdf: bool = Field(..., description="Whether source file was a PDF")
    page_count: int = Field(default=1, ge=1, description="Total document pages")
    metadata: MetadataModel = Field(..., description="Extracted metadata model")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_pipeline_output(self) -> IngestionOutput:
        """Convert into the canonical SPEC-02 IngestionOutput data contract."""
        return IngestionOutput(
            document_id=str(self.certificate_id),
            original_filename=self.metadata.original_filename,
            file_extension=self.original_file_path.suffix.lower(),
            mime_type=self.metadata.mime_type,
            file_size_bytes=self.metadata.file_size_bytes,
            raw_storage_path=str(self.working_image_path.resolve()),
            is_pdf=self.is_pdf,
            page_count=self.page_count,
        )


class IngestedDocumentResponse(BaseModel):
    """API response model for POST /api/v1/documents/upload."""

    document_id: str = Field(..., description="UUID string for the certificate")
    job_id: str = Field(..., description="UUID string for the processing job")
    status: str = Field(default="QUEUED", description="Initial processing status")
    created_at: datetime = Field(..., description="Ingestion timestamp")
    original_filename: str
    mime_type: str
    file_size_bytes: int
    sha256_checksum: str
    is_pdf: bool
    page_count: int
    image_width: int
    image_height: int
    suspicious_indicators: List[str] = Field(default_factory=list)
