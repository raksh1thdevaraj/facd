import io

from fastapi.testclient import TestClient
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.main import app

client = TestClient(app)


def test_upload_valid_png():
    img = Image.new("RGB", (900, 700), color=(250, 250, 250))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("certificate.png", buf.getvalue(), "image/png")},
    )

    assert response.status_code == 201
    data = response.json()
    assert "document_id" in data
    assert "job_id" in data
    assert data["status"] == "QUEUED"
    assert data["is_pdf"] is False
    assert data["image_width"] == 900
    assert data["image_height"] == 700
    assert len(data["sha256_checksum"]) == 64


def test_upload_valid_pdf():
    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=letter)
    c.drawString(100, 700, "Bachelor of Science in Computer Science")
    c.showPage()
    c.save()
    pdf_buf.seek(0)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("transcript.pdf", pdf_buf.getvalue(), "application/pdf")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["is_pdf"] is True
    assert data["page_count"] == 1
    assert data["image_width"] >= 2000


def test_upload_unsupported_file_type():
    txt_content = b"This is plain text and definitely not a certificate."
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", txt_content, "text/plain")},
    )

    assert response.status_code == 415
    data = response.json()
    assert data["error_code"] == "UNSUPPORTED_FILE_TYPE"


def test_upload_undersized_image():
    small_img = Image.new("RGB", (400, 300), color=(255, 255, 255))
    buf = io.BytesIO()
    small_img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("small.png", buf.getvalue(), "image/png")},
    )

    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "INSUFFICIENT_RESOLUTION"


def test_upload_corrupted_image():
    corrupt_bytes = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x12\x34" * 10
    )
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "CORRUPTED_FILE"


def test_ingestion_health_endpoint():
    response = client.get("/api/v1/health/ingestion")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "pdfium_available" in data
    assert "storage_writable" in data
    assert data["storage_writable"] is True
