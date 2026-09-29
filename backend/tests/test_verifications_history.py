"""Unit and integration tests for Verification History persistence and API endpoints."""

from __future__ import annotations

import json
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.verification_history import VerificationHistoryModel
from app.services.history_service import LEDGER_FILE, history_service


@pytest.fixture(autouse=True)
def clean_history_state(db_session: Session) -> Generator[None, None, None]:
    """Clean database table and json ledger before each test."""
    db_session.query(VerificationHistoryModel).delete()
    db_session.commit()
    history_service.clear_history(db_session)
    yield
    db_session.query(VerificationHistoryModel).delete()
    db_session.commit()
    history_service.clear_history(db_session)


def test_record_verification_persistence(db_session: Session) -> None:
    """Ensure verifications are persisted to both SQLite and data/history.json."""
    record = history_service.record_verification(
        record_id="hist-test-001",
        original_filename="vtu_marks_card_aarav.pdf",
        document_type="VTU_MARKSCARD",
        student_name="Aarav Sharma",
        identifier="1CR19CS001",
        issuer="Visvesvaraya Technological University",
        verdict="AUTHENTIC",
        confidence_score=0.985,
        qr_status=True,
        tampering_flags=[],
        remarks="All institutional security markers and marks match ground truth.",
        full_details={"sgpa": "9.45", "semester": "VIII"},
        db=db_session,
    )

    assert record["id"] == "hist-test-001"
    assert record["verdict"] == "AUTHENTIC"
    assert record["confidence_score"] == 0.985
    assert record["qr_status"] is True

    # Verify in SQLite
    db_row = db_session.query(VerificationHistoryModel).filter_by(id="hist-test-001").first()
    assert db_row is not None
    assert db_row.student_name == "Aarav Sharma"
    assert db_row.identifier == "1CR19CS001"
    assert db_row.verdict == "AUTHENTIC"

    # Verify in JSON ledger
    assert LEDGER_FILE.exists()
    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        ledger = json.load(f)
    assert any(item["id"] == "hist-test-001" for item in ledger)


def test_list_history_endpoint(client: TestClient, db_session: Session) -> None:
    """Test GET /api/verifications/history returns clean array, pagination headers, and sorting."""
    # Seed 3 records
    history_service.record_verification(
        record_id="rec-1",
        original_filename="vtu_01.pdf",
        document_type="VTU_MARKSCARD",
        student_name="Priya Patel",
        identifier="1MS20IS045",
        issuer="VTU",
        verdict="AUTHENTIC",
        confidence_score=0.96,
        qr_status=True,
        timestamp_iso="2026-09-20T10:00:00Z",
        db=db_session,
    )
    history_service.record_verification(
        record_id="rec-2",
        original_filename="coursera_cert.png",
        document_type="ONLINE_COURSE_CERTIFICATE",
        student_name="Rahul Verma",
        identifier="CRS-998877",
        issuer="Coursera",
        verdict="SUSPICIOUS",
        confidence_score=0.55,
        qr_status=False,
        tampering_flags=["Unaccredited Issuer Domain"],
        timestamp_iso="2026-09-21T10:00:00Z",
        db=db_session,
    )
    history_service.record_verification(
        record_id="rec-3",
        original_filename="fake_vtu.png",
        document_type="VTU_MARKSCARD",
        student_name="Devan Singh",
        identifier="1RV18EC012",
        issuer="VTU",
        verdict="FRAUDULENT",
        confidence_score=0.12,
        qr_status=False,
        tampering_flags=["Spliced CGPA", "Baseline Shift"],
        timestamp_iso="2026-09-22T10:00:00Z",
        db=db_session,
    )

    # 1. Fetch clean array (default format)
    response = client.get("/api/verifications/history?order=desc")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    # First item should be newest (rec-3)
    assert data[0]["id"] == "rec-3"
    assert data[0]["verdict"] == "FRAUDULENT"
    assert data[0]["student_name"] == "Devan Singh"

    # Verify pagination headers
    assert response.headers.get("X-Total-Count") == "3"
    assert response.headers.get("X-Page") == "1"

    # 2. Filter by verdict: AUTHENTIC
    res_auth = client.get("/api/verifications/history?verdict=AUTHENTIC")
    assert res_auth.status_code == 200
    data_auth = res_auth.json()
    assert len(data_auth) == 1
    assert data_auth[0]["id"] == "rec-1"
    assert data_auth[0]["student_name"] == "Priya Patel"

    # 3. Filter by search query (USN)
    res_search = client.get("/api/verifications/history?search=1MS20IS045")
    assert res_search.status_code == 200
    data_search = res_search.json()
    assert len(data_search) == 1
    assert data_search[0]["identifier"] == "1MS20IS045"

    # 4. Filter by student name specifically
    res_name = client.get("/api/verifications/history?student_name=Rahul")
    assert res_name.status_code == 200
    data_name = res_name.json()
    assert len(data_name) == 1
    assert data_name[0]["student_name"] == "Rahul Verma"

    # 5. Test paginated envelope format
    res_pag = client.get("/api/verifications/history?format=paginated&limit=2")
    assert res_pag.status_code == 200
    pag_data = res_pag.json()
    assert "items" in pag_data
    assert pag_data["total"] == 3
    assert pag_data["limit"] == 2
    assert len(pag_data["items"]) == 2


def test_get_history_detail_endpoint(client: TestClient, db_session: Session) -> None:
    """Test GET /api/verifications/history/{id} returns complete breakdown."""
    history_service.record_verification(
        record_id="detail-test-123",
        original_filename="stanford_online.png",
        document_type="ONLINE_COURSE_CERTIFICATE",
        student_name="Ananya Rao",
        identifier="STF-2026-X1",
        issuer="Stanford Online",
        verdict="AUTHENTIC",
        confidence_score=0.99,
        qr_status=True,
        tampering_flags=[],
        remarks="Cryptographic digital credential validated against provider registry.",
        full_details={
            "qr_verification": {"detected": True, "domain_valid": True},
            "rag_validation": {"schema_matched": True, "arithmetic_valid": True},
        },
        db=db_session,
    )

    response = client.get("/api/verifications/history/detail-test-123")
    assert response.status_code == 200
    detail = response.json()
    assert detail["id"] == "detail-test-123"
    assert detail["student_name"] == "Ananya Rao"
    assert detail["verdict"] == "AUTHENTIC"
    assert "full_details" in detail
    assert detail["full_details"]["qr_verification"]["detected"] is True

    # 404 for non-existent
    res_404 = client.get("/api/verifications/history/non-existent-uuid")
    assert res_404.status_code == 404


def test_delete_and_clear_history_endpoints(client: TestClient, db_session: Session) -> None:
    """Test DELETE /api/verifications/history/{id} and DELETE /api/verifications/history/clear."""
    history_service.record_verification(
        record_id="del-1",
        original_filename="doc1.png",
        document_type="VTU_MARKSCARD",
        verdict="AUTHENTIC",
        confidence_score=0.95,
        db=db_session,
    )
    history_service.record_verification(
        record_id="del-2",
        original_filename="doc2.png",
        document_type="VTU_MARKSCARD",
        verdict="SUSPICIOUS",
        confidence_score=0.60,
        db=db_session,
    )

    # Delete single item
    del_res = client.delete("/api/verifications/history/del-1")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify del-1 is gone
    check_res = client.get("/api/verifications/history/del-1")
    assert check_res.status_code == 404

    # Verify del-2 still exists
    list_res = client.get("/api/verifications/history")
    assert len(list_res.json()) == 1

    # Clear all
    clear_res = client.delete("/api/verifications/history/clear")
    assert clear_res.status_code == 200
    assert clear_res.json()["success"] is True

    # List is now empty
    empty_res = client.get("/api/verifications/history")
    assert len(empty_res.json()) == 0
