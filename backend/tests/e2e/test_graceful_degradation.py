"""Graceful degradation and fault-tolerant fallback recovery test (TC-E2E-04)."""

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_graceful_degradation_under_partial_failure(
    client: TestClient, db_session: Session, genuine_sample_path: Path
):
    """TC-E2E-04: Graceful degradation when template matching encounters
    simulated remote failure.
    """
    # 1. Simulate template verification failure using patch on the service class
    with patch(
        "app.modules.template_matching.service.TemplateVerificationService.verify",
        side_effect=RuntimeError("Simulated template matching timeout or crash"),
    ):
        with open(genuine_sample_path, "rb") as f:
            response = client.post(
                "/api/v1/certificates/upload",
                files={"file": (genuine_sample_path.name, f, "image/png")},
            )
        assert response.status_code == 202
        cert_id = response.json()["certificate_id"]

    # 2. Check certificate completed successfully despite simulated subsystem failure
    status_resp = client.get(f"/api/v1/certificates/{cert_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "COMPLETED"
    report_id = status_data["report_id"]
    assert report_id is not None

    # 3. Check report retrieval and explanation contains fallback advisory
    report_resp = client.get(f"/api/v1/reports/{report_id}")
    assert report_resp.status_code == 200
    report_data = report_resp.json()
    assert report_data["report_id"] == report_id
    assert report_data["verdict"] is not None
    report_text = (
        report_data.get("executive_summary", "") + str(report_data.get("findings", []))
    ).lower()
    assert "template" in report_text or "fallback" in report_text or "unverified" in report_text
