"""Integration tests for admin fraud analytics, system health, and history
filtering (TC-ADM-01 to TC-ADM-05).
"""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.certificate import CertificateModel
from app.models.report import VerificationReportModel
from app.models.template import InstitutionModel


def test_admin_analytics_summary(client: TestClient, db_session: Session):
    # Seed a sample certificate and report
    cert_id = str(uuid.uuid4())
    cert = CertificateModel(
        id=cert_id,
        file_path="dummy.png",
        file_hash="testhash123",
        original_filename="degree_test.png",
        file_size=1024,
        mime_type="image/png",
        job_status="COMPLETED",
        job_progress=100,
    )
    db_session.add(cert)

    report = VerificationReportModel(
        id=str(uuid.uuid4()),
        certificate_id=cert_id,
        verdict="MANIPULATED",
        overall_score=0.25,
        risk_score=75.0,
        confidence_score=0.92,
        sub_scores_json={},
        contributing_factors_json=[],
    )
    db_session.add(report)
    db_session.commit()

    resp = client.get("/api/v1/admin/analytics/summary?bypass_cache=true")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_certificates_verified"] >= 1
    assert data["total_manipulated_count"] >= 1
    assert data["overall_fraud_rate_percentage"] > 0
    assert len(data["daily_trends"]) == 30
    assert len(data["manipulation_modalities"]) >= 1


def test_admin_system_health(client: TestClient):
    resp = client.get("/api/v1/admin/system/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["db_status"] in ["ONLINE", "DEGRADED"]
    assert "db_latency_ms" in data
    assert "storage_used_gb" in data
    assert data["ocr_engine_status"] == "READY"
    assert "latency_breakdown" in data


def test_certificate_history_filtering_and_search(client: TestClient, db_session: Session):
    # Seed identifiable certificate
    cert_id = str(uuid.uuid4())
    cert = CertificateModel(
        id=cert_id,
        file_path="dummy.png",
        file_hash="unique_hash_xyz",
        original_filename="unique_harvard_diploma.pdf",
        file_size=2048,
        mime_type="application/pdf",
        job_status="COMPLETED",
        job_progress=100,
    )
    db_session.add(cert)

    rep = VerificationReportModel(
        id=str(uuid.uuid4()),
        certificate_id=cert_id,
        verdict="AUTHENTIC",
        overall_score=0.95,
        risk_score=5.0,
        confidence_score=0.98,
        sub_scores_json={},
        contributing_factors_json=[],
    )

    db_session.add(rep)
    db_session.commit()

    # 1. Search by filename
    search_resp = client.get("/api/v1/certificates?search=harvard")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert any("harvard" in item["filename"].lower() for item in search_data["items"])

    # 2. Filter by verdict
    verdict_resp = client.get("/api/v1/certificates?verdict=AUTHENTIC")
    assert verdict_resp.status_code == 200
    verdict_data = verdict_resp.json()
    assert all(item["verdict"] == "AUTHENTIC" for item in verdict_data["items"] if item["verdict"])


def test_institution_status_toggle(client: TestClient, db_session: Session):
    inst_id = str(uuid.uuid4())
    inst = InstitutionModel(
        id=inst_id,
        name="Apex University",
        code=f"APEX_{inst_id[:4]}",
        contact_email="registrar@apex.edu",
        is_active=True,
    )
    db_session.add(inst)
    db_session.commit()

    # Toggle to inactive
    resp = client.patch(f"/api/v1/institutions/{inst_id}/toggle-status")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # Toggle back to active
    resp2 = client.patch(f"/api/v1/institutions/{inst_id}/toggle-status")
    assert resp2.status_code == 200
    assert resp2.json()["is_active"] is True
