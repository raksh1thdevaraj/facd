"""Integration tests for audit logging service and API endpoints (TC-API-05)."""

import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.audit_log import AuditLogModel
from app.models.user import AppUserModel
from app.services.audit_service import AuditService


def test_audit_log_service_and_api(client: TestClient, db_session: Session):
    """Verify actions are logged to audit_logs and queryable via API (TC-API-05)."""
    # 0. Create admin user and auth header
    admin_user = AppUserModel(
        id="admin-test-01",
        email="admin_audit@test.com",
        full_name="Admin Audit",
        password_hash="hash",
        role="ADMIN",
        is_active=True,
    )
    db_session.add(admin_user)
    db_session.commit()
    admin_token = create_access_token(subject=admin_user.id, role="ADMIN")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Log direct action via service
    log_entry = AuditService.log_action(
        db=db_session,
        action="TEST_ACTION",
        certificate_id=None,
        ip_address="192.168.1.100",
        details={"test_key": "test_value"},
    )
    assert log_entry is not None
    assert log_entry.id is not None

    # 2. Trigger upload via API and check audit log
    buf = io.BytesIO()
    Image.new("RGB", (1200, 900), color=(255, 255, 255)).save(buf, format="PNG")
    buf.seek(0)
    files = {"file": ("audit_cert.png", buf, "image/png")}

    res = client.post("/api/v1/certificates/upload", files=files)
    assert res.status_code == 202
    cert_id = res.json()["certificate_id"]

    # Assert audit log exists in database
    db_log = (
        db_session.query(AuditLogModel)
        .filter_by(certificate_id=cert_id, action="CERTIFICATE_UPLOADED")
        .first()
    )
    assert db_log is not None
    assert db_log.details_json["filename"] == "audit_cert.png"

    # 3. Query GET /api/v1/audit-logs
    api_res = client.get("/api/v1/audit-logs?page=1&limit=10", headers=headers)
    assert api_res.status_code == 200
    data = api_res.json()
    assert data["total"] >= 2
    assert any(item["action"] == "CERTIFICATE_UPLOADED" for item in data["items"])

    # 4. Query with action filter
    filtered_res = client.get("/api/v1/audit-logs?action=TEST_ACTION", headers=headers)
    assert filtered_res.status_code == 200
    filtered_data = filtered_res.json()
    assert len(filtered_data["items"]) >= 1
    assert all(item["action"] == "TEST_ACTION" for item in filtered_data["items"])
