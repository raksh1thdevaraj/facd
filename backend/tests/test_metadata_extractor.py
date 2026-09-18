from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.modules.ingestion.metadata_extractor import MetadataExtractor


def test_clean_image_metadata_extraction(tmp_path: Path):
    img_path = tmp_path / "clean.png"
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    img.save(img_path, format="PNG")

    meta = MetadataExtractor.extract_image_metadata(img_path)
    assert meta["has_exif"] is False
    assert meta["software"] is None
    assert len(meta["suspicious_indicators"]) == 0


def test_image_with_photoshop_software_detected(tmp_path: Path):
    img_path = tmp_path / "edited.png"
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))

    # Add PNG text chunk with Photoshop software tag
    png_info = PngInfo()
    png_info.add_text("Software", "Adobe Photoshop 2024 (Windows)")
    img.save(img_path, format="PNG", pnginfo=png_info)

    meta = MetadataExtractor.extract_image_metadata(img_path)
    assert meta["software"] == "Adobe Photoshop 2024 (Windows)"
    assert any("Photoshop" in ind for ind in meta["suspicious_indicators"])


def test_pdf_metadata_extraction(tmp_path: Path):
    pdf_path = tmp_path / "doc.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    c.setCreator("Canva Certificate Builder")
    c.setProducer("ReportLab PDF Library")
    c.drawString(100, 700, "Official Certificate")
    c.showPage()
    c.save()

    meta = MetadataExtractor.extract_pdf_metadata(pdf_path)
    assert meta["page_count"] == 1
    assert "Canva" in (meta["software"] or "")
    assert any("Canva" in ind for ind in meta["suspicious_indicators"])
