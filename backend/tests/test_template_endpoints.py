import io
import uuid

import cv2
import numpy as np
from fastapi.testclient import TestClient


def _make_dummy_image_bytes() -> bytes:
    img = np.ones((200, 300, 3), dtype=np.uint8) * 200
    cv2.rectangle(img, (20, 20), (280, 180), (50, 50, 50), 2)
    _, buf = cv2.imencode(".png", img)
    return buf.tobytes()


def test_api_template_creation_and_listing(client: TestClient):
    """Verify POST /api/v1/templates registers template and GET /api/v1/templates lists it."""
    img_bytes = _make_dummy_image_bytes()

    response = client.post(
        "/api/v1/templates",
        data={
            "institution_name": "MIT",
            "template_name": "Standard MIT Diploma 2024",
            "degree_program": "B.S. in EECS",
            "effective_year_start": "2020",
            "effective_year_end": "2026",
            "seal_roi_json": '{"x": 10, "y": 10, "width": 50, "height": 50}',
        },
        files={"file": ("template.png", img_bytes, "image/png")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["template_name"] == "Standard MIT Diploma 2024"
    assert data["institution_name"] == "MIT"
    template_id = data["template_id"]

    # Test GET by ID
    get_resp = client.get(f"/api/v1/templates/{template_id}")
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["template_id"] == template_id
    assert detail["seal_roi"] == {"x": 10, "y": 10, "width": 50, "height": 50}

    # Test GET listing
    list_resp = client.get("/api/v1/templates")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) >= 1
    assert any(it["template_id"] == template_id for it in items)


def test_api_template_diagnostics(client: TestClient):
    """Verify GET /api/v1/templates/diagnostics returns health metrics."""
    resp = client.get("/api/v1/templates/diagnostics")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "storage_accessible" in data
    assert "index_query_latency_ms" in data


def test_api_records_bulk_import_and_query(client: TestClient):
    """Verify CSV bulk import and listing via /api/v1/records."""
    inst_id = str(uuid.uuid4())
    csv_data = """student_name,roll_number,degree_name,passing_year,cgpa
Alice Wonderland,WOND-001,Literature,2023,3.95
Mad Hatter,WOND-002,Chemistry,2023,3.70
"""

    import_resp = client.post(
        "/api/v1/records/bulk-import",
        data={"institution_id": inst_id},
        files={"file": ("records.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
    )
    assert import_resp.status_code == 200
    res = import_resp.json()
    assert res["records_inserted"] == 2
    assert res["duplicates_skipped"] == 0

    # Query records
    query_resp = client.get(f"/api/v1/records?institution_id={inst_id}")
    assert query_resp.status_code == 200
    records = query_resp.json()
    assert len(records) == 2
    assert any(r["roll_number"] == "WOND-001" for r in records)


def test_api_single_record_create(client: TestClient):
    """Verify POST /api/v1/records adds single student record."""
    inst_id = str(uuid.uuid4())
    payload = {
        "institution_id": inst_id,
        "student_name": "Tony Stark",
        "roll_number": "STARK-3000",
        "degree_name": "Mechanical & Electrical Engineering",
        "passing_year": 2024,
        "cgpa": 4.0,
        "issue_date": "2024-05-15",
    }

    resp = client.post("/api/v1/records", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["roll_number"] == "STARK-3000"

    # Duplicate roll number returns 409
    dup_resp = client.post("/api/v1/records", json=payload)
    assert dup_resp.status_code == 409
