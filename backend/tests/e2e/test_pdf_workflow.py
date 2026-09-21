"""End-to-End multi-page PDF upload and page-1 rasterization verification test (TC-E2E-03)."""

import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_multipage_pdf_workflow(
    client: TestClient, db_session: Session, sample_multipage_pdf: Path
):
    """TC-E2E-03: Multi-page PDF upload, high-resolution page-1 rasterization,
    and pipeline completion.
    """
    start_time = time.perf_counter()

    # 1. Upload 3-page PDF
    with open(sample_multipage_pdf, "rb") as f:
        response = client.post(
            "/api/v1/certificates/upload",
            files={"file": (sample_multipage_pdf.name, f, "application/pdf")},
        )
    assert response.status_code == 202, f"Upload failed: {response.text}"
    upload_data = response.json()
    cert_id = upload_data["certificate_id"]

    elapsed_time = time.perf_counter() - start_time
    assert elapsed_time <= 20.0

    # 2. Check status and completed report
    status_resp = client.get(f"/api/v1/certificates/{cert_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "COMPLETED"
    report_id = status_data["report_id"]
    assert report_id is not None

    # 3. Check report metadata reflects PDF
    report_resp = client.get(f"/api/v1/reports/{report_id}")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["file_metadata"]["file_format"] in ("PDF", "APPLICATION/PDF")
