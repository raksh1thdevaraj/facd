"""End-to-End full genuine certificate verification workflow test (TC-E2E-01)."""

import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_genuine_certificate_e2e_workflow(
    client: TestClient, db_session: Session, genuine_sample_path: Path
):
    """TC-E2E-01: Full workflow from upload of genuine document to
    authentic verdict and PDF report.
    """
    start_time = time.perf_counter()

    # 1. Upload genuine certificate
    with open(genuine_sample_path, "rb") as f:
        response = client.post(
            "/api/v1/certificates/upload",
            files={"file": (genuine_sample_path.name, f, "image/png")},
        )
    assert response.status_code == 202, f"Upload failed: {response.text}"
    upload_data = response.json()
    cert_id = upload_data["certificate_id"]
    assert cert_id is not None

    elapsed_time = time.perf_counter() - start_time

    # 2. Check performance budget (<= 15.0 seconds turnaround NFR-03)
    assert elapsed_time <= 15.0, f"Turnaround {elapsed_time:.2f}s exceeded 15s budget"

    # 3. Check certificate status polling endpoint
    status_resp = client.get(f"/api/v1/certificates/{cert_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "COMPLETED"
    assert status_data["progress"] == 100
    report_id = status_data["report_id"]
    assert report_id is not None

    # 4. Verify report retrieval endpoint & verdict
    report_resp = client.get(f"/api/v1/reports/{report_id}")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    print("\nDEBUG REPORT:", report_data)
    assert report_data["report_id"] == report_id
    assert report_data["verdict"] in ("AUTHENTIC", "SUSPICIOUS", "MANIPULATED")
    assert report_data["authenticity_score"] >= 0.50

    # 5. Verify downloadable PDF report endpoint
    pdf_resp = client.get(f"/api/v1/reports/{report_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000
