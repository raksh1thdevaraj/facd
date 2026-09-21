"""Integration tests for certificate management REST endpoints (TC-API-02)."""

import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.models.certificate import CertificateModel


def _create_dummy_image_bytes() -> io.BytesIO:
    buf = io.BytesIO()
    Image.new("RGB", (1200, 900), color=(250, 250, 250)).save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_certificate_upload_and_status_polling(client: TestClient):
    """Verify POST /upload returns HTTP 202 and status endpoint returns job state (TC-API-02)."""
    img_buf = _create_dummy_image_bytes()
    files = {"file": ("test_cert.png", img_buf, "image/png")}

    res = client.post("/api/v1/certificates/upload", files=files)
    assert res.status_code == 202
    data = res.json()
    assert "certificate_id" in data
    assert data["status"] == "PENDING"
    assert data["filename"] == "test_cert.png"
    assert len(data["file_hash"]) == 64

    cert_id = data["certificate_id"]

    # Poll status endpoint
    poll_res = client.get(f"/api/v1/certificates/{cert_id}/status")
    assert poll_res.status_code == 200
    status_data = poll_res.json()
    assert status_data["id"] == cert_id
    assert status_data["status"] in ("PENDING", "PROCESSING", "COMPLETED")
    assert 0 <= status_data["progress"] <= 100


def test_certificate_list_and_details(client: TestClient, db_session: Session):
    """Verify paginated listing and detailed retrieval of certificates."""
    cert = CertificateModel(
        id="cert-crud-101",
        file_path="/tmp/test.png",
        file_hash="11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff",
        original_filename="cert_sample.png",
        file_size=1024,
        mime_type="image/png",
        job_status="PENDING",
        job_progress=0,
    )
    db_session.add(cert)
    db_session.commit()

    # List endpoint
    res_list = client.get("/api/v1/certificates?page=1&limit=10")
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["total"] >= 1
    assert any(c["id"] == "cert-crud-101" for c in data["items"])

    # Detail endpoint
    res_detail = client.get("/api/v1/certificates/cert-crud-101")
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["id"] == "cert-crud-101"
    assert detail["filename"] == "cert_sample.png"


def test_certificate_deletion(client: TestClient, db_session: Session):
    """Verify DELETE /certificates/{id} deletes certificate record."""
    cert = CertificateModel(
        id="cert-delete-me",
        file_path="/tmp/nonexistent.png",
        file_hash="deadbeef",
        original_filename="to_delete.png",
        file_size=512,
        mime_type="image/png",
        job_status="FAILED",
    )
    db_session.add(cert)
    db_session.commit()

    del_res = client.delete("/api/v1/certificates/cert-delete-me")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    get_res = client.get("/api/v1/certificates/cert-delete-me")
    assert get_res.status_code == 404
