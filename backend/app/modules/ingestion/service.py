import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional

from PIL import Image

from app.config import settings
from app.modules.ingestion.fingerprint import compute_sha256
from app.modules.ingestion.metadata_extractor import MetadataExtractor
from app.modules.ingestion.rasterizer import PDFRasterizer
from app.modules.ingestion.storage_manager import StorageManager
from app.modules.ingestion.validator import IngestionValidator
from app.schemas.ingestion import IngestedDocument, MetadataModel

logger = logging.getLogger(__name__)


class DocumentIngestionService:
    """Orchestrates document validation, storage, fingerprinting, metadata, and rasterization."""

    def __init__(
        self,
        storage: Optional[StorageManager] = None,
        validator: Optional[IngestionValidator] = None,
    ):
        self.storage = storage or StorageManager()
        self.validator = validator or IngestionValidator()

    def ingest(
        self,
        file_stream: BinaryIO,
        original_filename: str,
        client_ip: str = "127.0.0.1",
    ) -> IngestedDocument:
        """Process an uploaded certificate stream end-to-end.

        Cleans up any created files on disk if an error occurs.
        """
        start_time = time.perf_counter()
        cert_id = uuid.uuid4()

        # 1. Validate magic bytes and MIME type
        mime_type = self.validator.validate_file_signature(file_stream, original_filename)

        # 2. Validate file size limits
        file_stream.seek(0, 2)  # seek to end
        size_bytes = file_stream.tell()
        file_stream.seek(0)
        self.validator.validate_file_size(size_bytes, settings.MAX_UPLOAD_SIZE_BYTES)

        # 3. Store raw upload stream using UUID filename
        record = self.storage.save_upload_stream(
            file_stream=file_stream,
            original_filename=original_filename,
            certificate_id=cert_id,
        )
        stored_path = record.stored_file_path

        try:
            # 4. Verify file integrity and dimensions
            width, height = self.validator.validate_image_integrity(stored_path, mime_type)
            is_pdf = mime_type == "application/pdf" or stored_path.suffix.lower() == ".pdf"

            if not is_pdf:
                # Direct image dimension check
                width, height = self.validator.validate_dimensions(width, height)

            # 5. Compute SHA-256 fingerprint
            sha256_hash = compute_sha256(stored_path)

            # 6. Extract document metadata & EXIF
            meta_dict = MetadataExtractor.extract(stored_path, mime_type)

            # 7. Rasterize if PDF
            working_image_path: Path
            page_count = 1

            if is_pdf:
                rasterized_pages = PDFRasterizer.rasterize_pdf(
                    pdf_path=stored_path,
                    output_dir=self.storage.rasterized_dir,
                    dpi=300,
                    max_pages=3,
                )
                working_image_path = rasterized_pages[0]
                page_count = len(rasterized_pages)

                # Inspect dimensions of rasterized page
                with Image.open(working_image_path) as page_img:
                    width, height = page_img.size
                self.validator.validate_dimensions(width, height)
            else:
                working_image_path = stored_path

            # Format normalized format label
            doc_format = "PDF" if is_pdf else (mime_type.split("/")[-1].upper())

            # 8. Assemble domain models
            metadata_model = MetadataModel(
                file_size_bytes=size_bytes,
                mime_type=mime_type,
                original_filename=record.original_filename,
                sha256_checksum=sha256_hash,
                image_width=width,
                image_height=height,
                software_signature=meta_dict.get("software"),
                creation_date=meta_dict.get("creation_date"),
                modification_date=meta_dict.get("modification_date"),
                has_exif=meta_dict.get("has_exif", False),
                raw_metadata=meta_dict.get("raw_metadata", {}),
                suspicious_indicators=meta_dict.get("suspicious_indicators", []),
            )

            ingested_doc = IngestedDocument(
                certificate_id=cert_id,
                original_file_path=stored_path,
                working_image_path=working_image_path,
                format=doc_format,
                is_pdf=is_pdf,
                page_count=page_count,
                metadata=metadata_model,
                created_at=datetime.utcnow(),
            )

            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Successfully ingested document %s (%s, %d bytes) in %.2f ms from %s",
                cert_id,
                mime_type,
                size_bytes,
                duration_ms,
                client_ip,
            )

            return ingested_doc

        except Exception:
            # Clean up all created files on failure (No orphan files)
            self.storage.delete_certificate_files(cert_id)
            raise


# Global singleton instance provider
_ingestion_service_instance: Optional[DocumentIngestionService] = None


def get_ingestion_service() -> DocumentIngestionService:
    """Dependency provider for FastAPI route handlers."""
    global _ingestion_service_instance
    if _ingestion_service_instance is None:
        _ingestion_service_instance = DocumentIngestionService()
    return _ingestion_service_instance
