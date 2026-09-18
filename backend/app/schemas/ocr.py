from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.pipeline import CertificateFields, OCROutput, OCRToken
from app.schemas.primitives import BoundingBox, PixelBoundingBox


class OCRConfig(BaseModel):
    """Configuration options for OCR processing."""

    engine: str = Field(
        default="easyocr",
        description="OCR engine backend: 'easyocr', 'pytesseract', or 'mock'",
    )
    languages: List[str] = Field(default=["en"], description="Language codes for OCR")
    confidence_threshold: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Threshold below which fields are flagged for manual review",
    )
    generate_overlay: bool = Field(
        default=True,
        description="Whether to generate an annotated visual overlay image",
    )
    use_binarized_image: bool = Field(
        default=False,
        description="Whether to use binarized image instead of enhanced RGB image",
    )
    gpu: bool = Field(
        default=False,
        description="Whether to attempt GPU acceleration (auto-fallback to CPU)",
    )


class ExtractedFieldDTO(BaseModel):
    """Structured representation of an extracted academic certificate entity."""

    field_name: str
    value: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    is_flagged: bool = False
    bbox: Optional[BoundingBox] = None
    pixel_bbox: Optional[PixelBoundingBox] = None


class OCRResultDTO(BaseModel):
    """High-level Data Transfer Object summarizing the OCR extraction results."""

    document_id: str
    engine_used: str
    average_ocr_confidence: float = Field(..., ge=0.0, le=1.0)
    low_confidence_flag: bool = False
    raw_extracted_text: str
    token_count: int
    fields: CertificateFields
    field_details: Dict[str, ExtractedFieldDTO] = Field(default_factory=dict)
    overlay_path: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_pipeline_output(self, tokens: Optional[List[OCRToken]] = None) -> OCROutput:
        """Convert to canonical SPEC-02 OCROutput pipeline contract."""
        return OCROutput(
            document_id=self.document_id,
            engine_used=self.engine_used,
            raw_extracted_text=self.raw_extracted_text,
            average_ocr_confidence=self.average_ocr_confidence,
            tokens=tokens or [],
            fields=self.fields,
            low_confidence_flag=self.low_confidence_flag,
        )
