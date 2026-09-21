"""Integration tests for institution onboarding and bulk CSV records endpoints."""

import io

from fastapi.testclient import TestClient


def test_institution_endpoints_lifecycle(client: TestClient):
    """Verify university registration, listing, and bulk CSV student record import."""
    # 1. Register new institution
    inst_payload = {
        "name": "State University of Technology",
        "code": "SUT",
        "contact_email": "registrar@sut.edu",
    }
    res = client.post("/api/v1/institutions", json=inst_payload)
    assert res.status_code == 201
    inst_data = res.json()
    assert inst_data["name"] == "State University of Technology"
    assert inst_data["code"] == "SUT"
    inst_id = inst_data["id"]

    # 2. Duplicate registration returns 409
    res_dup = client.post("/api/v1/institutions", json=inst_payload)
    assert res_dup.status_code == 409

    # 3. List institutions
    list_res = client.get("/api/v1/institutions")
    assert list_res.status_code == 200
    assert any(i["id"] == inst_id for i in list_res.json()["items"])

    # 4. Get specific institution
    get_res = client.get(f"/api/v1/institutions/{inst_id}")
    assert get_res.status_code == 200
    assert get_res.json()["code"] == "SUT"

    # 5. Bulk CSV upload
    csv_content = (
        "student_name,roll_number,degree_name,passing_year,cgpa\n"
        "John Doe,SUT-2024-001,B.Sc Computer Science,2024,8.9\n"
        "Mary Jane,SUT-2024-002,B.Eng Electrical,2024,9.2\n"
    )
    csv_file = io.BytesIO(csv_content.encode("utf-8"))
    files = {"file": ("students.csv", csv_file, "text/csv")}

    bulk_res = client.post(f"/api/v1/institutions/{inst_id}/records/bulk", files=files)
    assert bulk_res.status_code == 201
    bulk_data = bulk_res.json()
    assert bulk_data["imported_count"] == 2
    assert bulk_data["status"] == "SUCCESS"
