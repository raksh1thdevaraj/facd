from pathlib import Path

import pypdf
import pytest
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.core.exceptions import EncryptedPdfError
from app.modules.ingestion.rasterizer import PDFRasterizer


def create_test_pdf(output_path: Path, num_pages: int = 1) -> Path:
    """Helper to generate a clean multi-page test PDF using ReportLab."""
    c = canvas.Canvas(str(output_path), pagesize=letter)
    for i in range(num_pages):
        c.setFont("Helvetica-Bold", 24)
        c.drawString(100, 700, f"Certificate of Degree - Page {i + 1}")
        c.setFont("Helvetica", 14)
        c.drawString(100, 650, "Official test document for academic certificate verification.")
        c.showPage()
    c.save()
    return output_path


def create_encrypted_pdf(input_pdf: Path, encrypted_path: Path, password: str = "secret") -> Path:
    """Helper to encrypt a PDF using pypdf."""
    reader = pypdf.PdfReader(str(input_pdf))
    writer = pypdf.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    with open(encrypted_path, "wb") as f:
        writer.write(f)
    return encrypted_path


def test_rasterize_single_page_pdf(tmp_path: Path):
    pdf_path = create_test_pdf(tmp_path / "cert.pdf", num_pages=1)
    out_dir = tmp_path / "rasterized"

    pages = PDFRasterizer.rasterize_pdf(pdf_path, out_dir, dpi=300)
    assert len(pages) == 1
    assert pages[0].exists()

    with Image.open(pages[0]) as img:
        # Standard Letter page (8.5 x 11 in) at 300 DPI is 2550 x 3300 px
        w, h = img.size
        assert w >= 2000
        assert h >= 2500


def test_rasterize_multipage_pdf_respects_max_pages(tmp_path: Path):
    pdf_path = create_test_pdf(tmp_path / "multipage.pdf", num_pages=4)
    out_dir = tmp_path / "rasterized_multi"

    pages = PDFRasterizer.rasterize_pdf(pdf_path, out_dir, dpi=300, max_pages=2)
    assert len(pages) == 2


def test_encrypted_pdf_raises_encrypted_error(tmp_path: Path):
    clean_pdf = create_test_pdf(tmp_path / "clean.pdf", num_pages=1)
    enc_pdf = create_encrypted_pdf(clean_pdf, tmp_path / "protected.pdf", "pass123")
    out_dir = tmp_path / "rasterized_enc"

    with pytest.raises(EncryptedPdfError):
        PDFRasterizer.rasterize_pdf(enc_pdf, out_dir, dpi=300)
