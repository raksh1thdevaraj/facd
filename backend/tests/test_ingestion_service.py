import io
from pathlib import Path

import pytest
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.core.exceptions import InsufficientResolutionError
from app.modules.ingestion.service import DocumentIngestionService
from app.modules.ingestion.storage_manager import StorageManager


def test_ingest_valid_png_document(tmp_path: Path):
    storage = StorageManager(base_dir=tmp_path / "storage")
    service = DocumentIngestionService(storage=storage)

    # Create 800x600 PNG in memory
    img = Image.new("RGB", (1000, 750), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    ingested = service.ingest(buf, "sample_cert.png")

    assert ingested.is_pdf is False
    assert ingested.page_count == 1
    assert ingested.format == "PNG"
    assert ingested.metadata.image_width == 1000
    assert ingested.metadata.image_height == 750
    assert len(ingested.metadata.sha256_checksum) == 64
    assert ingested.original_file_path.exists()
    assert ingested.working_image_path.exists()

    # Verify SPEC-02 pipeline data contract mapping
    pipeline_output = ingested.to_pipeline_output()
    assert pipeline_output.document_id == str(ingested.certificate_id)
    assert pipeline_output.original_filename == "sample_cert.png"
    assert pipeline_output.file_extension == ".png"
    assert pipeline_output.mime_type == "image/png"
    assert pipeline_output.is_pdf is False


def test_ingest_valid_pdf_document(tmp_path: Path):
    storage = StorageManager(base_dir=tmp_path / "storage")
    service = DocumentIngestionService(storage=storage)

    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=letter)
    c.drawString(100, 700, "Official Degree of Engineering")
    c.showPage()
    c.save()
    pdf_buf.seek(0)

    ingested = service.ingest(pdf_buf, "degree.pdf")

    assert ingested.is_pdf is True
    assert ingested.page_count == 1
    assert ingested.format == "PDF"
    assert ingested.working_image_path.suffix == ".png"
    assert ingested.working_image_path.exists()
    assert ingested.metadata.image_width >= 2000


def test_orphan_file_cleanup_on_failure(tmp_path: Path):
    storage = StorageManager(base_dir=tmp_path / "storage")
    service = DocumentIngestionService(storage=storage)

    # Undersized image (500x500) will fail dimension validation after saving
    img = Image.new("RGB", (500, 500), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    with pytest.raises(InsufficientResolutionError):
        service.ingest(buf, "too_small.png")

    # Verify that raw upload directory contains 0 orphan files
    raw_files = list(storage.raw_dir.glob("*"))
    assert len(raw_files) == 0


def test_path_traversal_filename_sanitization(tmp_path: Path):
    storage = StorageManager(base_dir=tmp_path / "storage")
    service = DocumentIngestionService(storage=storage)

    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    # Filename with path traversal payload
    traversal_name = "../../../etc/passwd.png"
    ingested = service.ingest(buf, traversal_name)

    # Must be safely stored within raw_dir
    assert ingested.original_file_path.is_relative_to(storage.raw_dir)
    assert ingested.original_file_path.name.endswith(".png")
    assert "passwd" not in str(ingested.original_file_path)
