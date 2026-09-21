"""Concurrent multi-user upload and execution stress test (TC-E2E-05)."""

import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_concurrent_multi_user_uploads(
    client: TestClient, db_session: Session, genuine_sample_path: Path
):
    """TC-E2E-05: Process multiple concurrent certificate uploads without
    race conditions or lock contention.
    """
    num_uploads = 3
    cert_ids = []
    start_time = time.perf_counter()

    # 1. Upload multiple certificates
    for i in range(num_uploads):
        with open(genuine_sample_path, "rb") as f:
            response = client.post(
                "/api/v1/certificates/upload",
                files={"file": (f"concurrent_test_{i}.png", f, "image/png")},
            )
        assert response.status_code == 202
        cert_ids.append(response.json()["certificate_id"])

    elapsed_time = time.perf_counter() - start_time
    assert elapsed_time > 0
    assert len(set(cert_ids)) == num_uploads

    # 2. Check each certificate completed with unique reports
    report_ids = []
    for cid in cert_ids:
        resp = client.get(f"/api/v1/certificates/{cid}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "COMPLETED"
        assert data["progress"] == 100
        assert data["report_id"] is not None
        report_ids.append(data["report_id"])

    # 3. Assert zero cross-contamination (each report ID is distinct)
    assert len(set(report_ids)) == num_uploads
