"""
Automated Test Suite: Two-Role Academic & Course Certificate Verification System.
Validates:
1. Unauthenticated rejection (401 Unauthorized) across verification and admin endpoints
2. Role-Based Access Control (403 Forbidden for non-admin accessing admin console)
3. Authenticated Verifier Hub (/api/v1/verify) for Marks Cards and Course Certificates
4. Forensic cards breakdown (QR validation, layout alignment, template integrity, metadata)
5. Latency SLA constraint (<250ms on CPU)
6. Admin Supervisory Telemetry (4 KPI Cards + ML Performance Benchmarks)
7. Behavioral Anomaly Monitor (Khormi et al., IEEE 2026)
8. Scans Ledger with multi-attribute filtering
"""

import os
import sys
import pytest
import numpy as np
import cv2
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root and backend in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.main import app
from app.database import SessionLocal
from app.models.user import AppUserModel
from app.core.security import create_access_token, get_password_hash
from src.verify_certificate import CertificateVerifier, get_certificate_verifier
from src.behavioral_monitor import BehavioralMonitor


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_headers():
    db = SessionLocal()
    try:
        user = db.query(AppUserModel).filter(AppUserModel.email == "verifier_test@certishield.ai").first()
        if not user:
            user = AppUserModel(
                email="verifier_test@certishield.ai",
                full_name="Standard Verifier User",
                password_hash=get_password_hash("Verifier@123"),
                role="user",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        token = create_access_token(subject=user.id, role="user")
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


@pytest.fixture
def admin_headers():
    db = SessionLocal()
    try:
        admin = db.query(AppUserModel).filter(AppUserModel.email == "admin_test@certishield.ai").first()
        if not admin:
            admin = AppUserModel(
                email="admin_test@certishield.ai",
                full_name="Supervisory Administrator",
                password_hash=get_password_hash("Admin@123456"),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
        token = create_access_token(subject=admin.id, role="admin")
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()


@pytest.fixture
def sample_image():
    img_path = Path("datasets/synthetic_manipulated/genuine/GEN_00001.png")
    if img_path.exists():
        return cv2.imread(str(img_path))
    # Fallback synthetic clean certificate canvas
    canvas = np.ones((768, 1024, 3), dtype=np.uint8) * 255
    cv2.putText(canvas, "Heritage University", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    return canvas


def test_unauthenticated_verification_rejected(client, sample_image):
    """Ensure unauthenticated requests to /api/v1/verify return HTTP 401 Unauthorized."""
    _, encoded_img = cv2.imencode(".png", sample_image)
    files = {"file": ("test.png", encoded_img.tobytes(), "image/png")}
    data = {"certificate_type": "marks_card"}

    response = client.post("/api/v1/verify", files=files, data=data)
    assert response.status_code == 401, "Unauthenticated verification must be rejected with 401"


def test_unauthenticated_admin_telemetry_rejected(client):
    """Ensure unauthenticated requests to /api/v1/admin/telemetry return HTTP 401 Unauthorized."""
    response = client.get("/api/v1/admin/telemetry")
    assert response.status_code == 401, "Unauthenticated admin telemetry must return 401"


def test_user_forbidden_from_admin_telemetry(client, user_headers):
    """Ensure standard 'user' role is blocked from admin console (403 Forbidden)."""
    response = client.get("/api/v1/admin/telemetry", headers=user_headers)
    assert response.status_code == 403, "Non-admin user role must be blocked from admin telemetry"


def test_public_sample_scenarios_endpoint(client):
    """Ensure pre-configured sample schema endpoint remains accessible."""
    response = client.get("/api/v1/verify/sample-data")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4


def test_public_verification_genuine_certificate(client, user_headers, sample_image):
    """Test authenticated verification on genuine document, asserting forensic cards and SLA."""
    # Encode sample image to bytes
    _, encoded_img = cv2.imencode(".png", sample_image)
    files = {"file": ("test_genuine.png", encoded_img.tobytes(), "image/png")}
    data = {
        "certificate_type": "marks_card",
        "expected_student_name": "Aarav Sharma",
        "expected_reg_no": "HTU2022-CS-041",
    }

    response = client.post("/api/v1/verify", files=files, data=data, headers=user_headers)
    assert response.status_code == 200
    res = response.json()

    # Core response contract
    assert "scan_id" in res
    assert "final_status" in res
    assert res["final_status"] in ["VERIFIED", "SUSPICIOUS", "REJECTED"]
    assert "confidence_score" in res
    assert 0.0 <= res["confidence_score"] <= 1.0
    assert "latency_ms" in res
    assert res["latency_ms"] < 250.0, f"Latency SLA violated: {res['latency_ms']}ms >= 250ms"

    # 4 Forensic Cards
    cards = res.get("forensic_cards", {})
    assert "qr_and_url" in cards
    assert "layout_alignment" in cards
    assert "template_integrity" in cards
    assert "metadata_checks" in cards

    # DIAR-AI Template check
    template_info = cards["template_integrity"]
    assert "ssim_score" in template_info
    assert "edge_diff_ratio" in template_info


def test_public_verification_course_certificate(client, user_headers, sample_image):
    """Verify course certificate endpoint handling and accreditation validation."""
    _, encoded_img = cv2.imencode(".png", sample_image)
    files = {"file": ("course_cert.png", encoded_img.tobytes(), "image/png")}
    data = {
        "certificate_type": "course_certificate",
    }

    response = client.post("/api/v1/verify", files=files, data=data, headers=user_headers)
    assert response.status_code == 200
    res = response.json()
    assert res["certificate_type"] == "course_certificate"
    assert "verdict_badge" in res


def test_admin_telemetry_four_kpis(client, admin_headers):
    """Test GET /api/v1/admin/telemetry returns the 4 mandatory KPI cards and model metrics for admin."""
    response = client.get("/api/v1/admin/telemetry", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()

    # 4 Mandatory KPI Cards
    kpis = data["kpi_cards"]
    assert "total_verifications" in kpis
    assert "active_users" in kpis
    assert "system_accuracy" in kpis
    assert "flagged_anomalies" in kpis

    assert kpis["total_verifications"]["value"] >= 0
    assert kpis["active_users"]["value"] >= 1
    assert "%" in str(kpis["system_accuracy"]["value"])

    # Model Performance
    perf = data["model_performance"]
    assert "visual_forensics" in perf
    assert "behavioral_fraud" in perf
    assert "latency" in perf
    assert perf["latency"]["sla_met"] is True


def test_admin_behavioral_logs_stream(client, admin_headers):
    """Verify Khormi et al. registrar behavioral anomaly monitor endpoint for admin."""
    response = client.get("/api/v1/admin/behavioral-logs?limit=10", headers=admin_headers)
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) > 0

    first = logs[0]
    assert "user_id" in first
    assert "timestamp" in first
    assert "threat_level" in first
    assert first["threat_level"] in ["CRITICAL", "ELEVATED", "NORMAL"]
    assert "risk_score" in first
    assert "flags" in first


def test_admin_scans_ledger_filtering(client, admin_headers):
    """Test filtering verification scans by status and certificate type for admin."""
    response = client.get("/api/v1/admin/scans?limit=20", headers=admin_headers)
    assert response.status_code == 200
    scans = response.json()
    assert isinstance(scans, list)

    # Test status filter
    response_ver = client.get("/api/v1/admin/scans?status_filter=VERIFIED", headers=admin_headers)
    assert response_ver.status_code == 200
    for s in response_ver.json():
        assert s["final_status"] == "VERIFIED"


def test_behavioral_monitor_engine():
    """Unit test BehavioralMonitor evaluating normal vs compromised events."""
    monitor = BehavioralMonitor(model_path="models/behavioral_fraud_model.pkl")

    # Normal office hour campus event
    normal = monitor.evaluate_event(
        timestamp="2026-09-22 14:30:00",
        source_ip="10.10.1.50",
        device_type="Desktop_Workstation",
        location="Registrar_Office",
        action="ISSUE_CERTIFICATE",
        user_id="STAFF_001",
    )
    assert normal["threat_level"] == "NORMAL"
    assert normal["risk_score"] < 50.0

    # Compromised off-hours external IP event
    anomalous = monitor.evaluate_event(
        timestamp="2026-09-22 03:15:00",
        source_ip="198.51.100.24",
        device_type="Tor_Browser",
        location="Registrar_Office",
        action="DELETE_RECORD",
        user_id="COMPROMISED_001",
    )
    assert anomalous["threat_level"] == "CRITICAL"
    assert anomalous["risk_score"] >= 80.0
    assert len(anomalous["flags"]) > 0
