"""Integration tests for verification report FastAPI endpoints (TC-REP-05)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.report_generator.service import ReportService
from app.modules.score_fusion.service import ScoreFusionService
from app.schemas.pipeline import CertificateFields


def test_api_report_endpoints_lifecycle(client: TestClient, db_session: Session):
    """Verify GET /api/v1/reports/{id}, /json, /pdf, and /verify endpoints (TC-REP-05)."""
    # 1. Generate a test report in DB
    service = ReportService()
    fusion = ScoreFusionService()
    decision = fusion.fuse_and_decide(
        certificate_id="cert-api-rep-001",
        visual_fake_prob=0.08,
        tabular_fake_prob=0.05,
        forensic_score=0.92,
        text_consistency_score=0.96,
        template_score=0.95,
        tier_status="TIER_1_VERIFIED",
    )

    report = service.generate_report(
        certificate_id="cert-api-rep-001",
        decision=decision,
        extracted_fields=CertificateFields(
            student_name="David Warner",
            register_number="REG-DW-1234",
            institution_name="Global University",
        ),
        db=db_session,
    )
    rep_id = report.report_id

    # 2. Test GET /api/v1/reports/{report_id}
    res_json = client.get(f"/api/v1/reports/{rep_id}")
    assert res_json.status_code == 200
    data = res_json.json()
    assert data["report_id"] == rep_id
    assert data["certificate_id"] == "cert-api-rep-001"
    assert data["verdict"] == "AUTHENTIC"
    assert data["extracted_fields"]["student_name"] == "David Warner"

    # 3. Test GET /api/v1/reports/{report_id}/json (Download attachment)
    res_dl_json = client.get(f"/api/v1/reports/{rep_id}/json")
    assert res_dl_json.status_code == 200
    assert "attachment" in res_dl_json.headers.get("Content-Disposition", "")
    assert res_dl_json.json()["report_id"] == rep_id

    # 4. Test GET /api/v1/reports/{report_id}/pdf (Download PDF)
    res_pdf = client.get(f"/api/v1/reports/{rep_id}/pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF-")

    # 5. Test GET /api/v1/reports/{report_id}/verify (Check digital signature)
    res_verify = client.get(f"/api/v1/reports/{rep_id}/verify")
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert verify_data["is_authentic_and_unaltered"] is True
    assert verify_data["report_id"] == rep_id
    assert verify_data["verdict"] == "AUTHENTIC"

    # 6. Test 404 on nonexistent report
    res_404 = client.get("/api/v1/reports/nonexistent-report-uuid-000")
    assert res_404.status_code == 404
