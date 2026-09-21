"""End-to-End manipulated certificate verification workflow test (TC-E2E-02)."""

import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_manipulated_certificate_e2e_workflow(
    client: TestClient, db_session: Session, manipulated_sample_path: Path
):
    """TC-E2E-02: Full workflow from upload of forged certificate to
    manipulated/suspicious verdict and evidence.
    """
    start_time = time.perf_counter()

    # 1. Upload manipulated certificate
    with open(manipulated_sample_path, "rb") as f:
        response = client.post(
            "/api/v1/certificates/upload",
            files={"file": (manipulated_sample_path.name, f, "image/png")},
        )
    assert response.status_code == 202, f"Upload failed: {response.text}"
    upload_data = response.json()
    cert_id = upload_data["certificate_id"]
    assert cert_id is not None

    elapsed_time = time.perf_counter() - start_time
    assert elapsed_time <= 15.0

    # 2. Check status
    status_resp = client.get(f"/api/v1/certificates/{cert_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "COMPLETED"
    report_id = status_data["report_id"]
    assert report_id is not None

    # 3. Check report retrieval and verdict
    report_resp = client.get(f"/api/v1/reports/{report_id}")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["report_id"] == report_id
    assert report_data["verdict"] in ("MANIPULATED", "SUSPICIOUS")
    assert report_data["risk_score"] >= 30.0 or report_data["authenticity_score"] <= 0.70
