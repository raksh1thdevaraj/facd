import uuid

from sqlalchemy.orm import Session

from app.models.record import InstitutionRecordModel
from app.modules.template_matching.record_importer import import_records_from_csv


def test_import_records_from_csv_success(db_session: Session):
    """Verify standard CSV import parses records and bulk-inserts into database."""
    inst_id = str(uuid.uuid4())
    csv_content = """student_name,roll_number,degree_name,passing_year,cgpa,issue_date
John Doe,CS2020-001,Computer Science,2024,3.85,2024-06-15
Jane Smith,CS2020-002,Computer Science,2024,3.92,2024-06-15
Bob Johnson,EE2020-010,Electrical Engineering,2024,3.40,2024-06-15
"""

    resp = import_records_from_csv(csv_content, inst_id, db_session)

    assert resp.total_records_processed == 3
    assert resp.records_inserted == 3
    assert resp.duplicates_skipped == 0
    assert len(resp.errors) == 0

    records = (
        db_session.query(InstitutionRecordModel)
        .filter(InstitutionRecordModel.institution_id == inst_id)
        .all()
    )
    assert len(records) == 3


def test_import_records_skips_duplicates(db_session: Session):
    """Verify duplicate roll numbers within the same institution are skipped."""
    inst_id = str(uuid.uuid4())
    # Existing record in database
    existing = InstitutionRecordModel(
        id=str(uuid.uuid4()),
        institution_id=inst_id,
        student_name="Original Name",
        roll_number="DUPLICATE-01",
        degree_name="Physics",
        passing_year=2023,
    )
    db_session.add(existing)
    db_session.commit()

    csv_content = """student_name,roll_number,degree_name,passing_year
New Person,DUPLICATE-01,Physics,2023
Valid Person,UNIQUE-02,Chemistry,2023
"""

    resp = import_records_from_csv(csv_content, inst_id, db_session)

    assert resp.records_inserted == 1
    assert resp.duplicates_skipped == 1


def test_import_records_missing_required_columns(db_session: Session):
    """Verify CSV with missing columns reports error."""
    inst_id = str(uuid.uuid4())
    csv_content = """student_name,random_col
John Doe,12345
"""

    resp = import_records_from_csv(csv_content, inst_id, db_session)

    assert resp.records_inserted == 0
    assert any("Required CSV columns missing" in e for e in resp.errors)
