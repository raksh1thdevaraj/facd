import uuid

from sqlalchemy.orm import Session

from app.models.record import InstitutionRecordModel
from app.modules.template_matching.record_verifier import verify_student_record
from app.schemas.pipeline import CertificateFields


def test_tc_tmp_03_exact_record_match(db_session: Session):
    """TC-TMP-03: Exact student record match confirms all authentic fields."""
    inst_id = str(uuid.uuid4())
    rec = InstitutionRecordModel(
        id=str(uuid.uuid4()),
        institution_id=inst_id,
        student_name="ALICE ELIZABETH DOE",
        roll_number="CS2020-0042",
        degree_name="Bachelor of Science in Computer Science",
        passing_year=2024,
        cgpa=3.85,
        issue_date="2024-06-15",
    )
    db_session.add(rec)
    db_session.commit()

    fields = CertificateFields(
        student_name="Alice Elizabeth Doe",
        register_number="CS2020-0042",
        course_degree="Bachelor of Science in Computer Science",
        grade_or_marks="3.85",
        issue_date="June 15, 2024",
    )

    result = verify_student_record(fields, db_session, institution_id=inst_id)

    assert result.record_found is True
    assert result.matched_record_id == str(rec.id)
    assert result.name_match_score >= 0.85
    assert result.roll_no_match is True
    assert result.degree_match is True
    assert result.passing_year_match is True
    assert result.cgpa_match is True
    assert len(result.discrepancies) == 0


def test_tc_tmp_04_mismatched_record_name_contradiction(db_session: Session):
    """TC-TMP-04: Mismatched student record: name contradicts roll number in database."""
    inst_id = str(uuid.uuid4())
    rec = InstitutionRecordModel(
        id=str(uuid.uuid4()),
        institution_id=inst_id,
        student_name="JOHN FITZGERALD SMITH",
        roll_number="EE2019-0105",
        degree_name="Bachelor of Electrical Engineering",
        passing_year=2023,
        cgpa=3.50,
    )
    db_session.add(rec)
    db_session.commit()

    # Fraudulent cert with different student name claiming this roll number
    fields = CertificateFields(
        student_name="MICHAEL BRANDON CLARK",
        register_number="EE2019-0105",
        course_degree="Bachelor of Electrical Engineering",
        grade_or_marks="3.50",
        issue_date="2023-05-20",
    )

    result = verify_student_record(fields, db_session, institution_id=inst_id)

    assert result.record_found is True
    assert result.name_match_score < 0.60
    assert result.roll_no_match is True
    assert any("does not match university record" in d for d in result.discrepancies)


def test_tc_tmp_04_mismatched_cgpa_contradiction(db_session: Session):
    """TC-TMP-04: Fraudulent marks: student bumped CGPA from 3.20 to 3.95."""
    inst_id = str(uuid.uuid4())
    rec = InstitutionRecordModel(
        id=str(uuid.uuid4()),
        institution_id=inst_id,
        student_name="SARAH CONNOR",
        roll_number="ME2021-0088",
        degree_name="Mechanical Engineering",
        passing_year=2024,
        cgpa=3.20,
    )
    db_session.add(rec)
    db_session.commit()

    fields = CertificateFields(
        student_name="Sarah Connor",
        register_number="ME2021-0088",
        course_degree="Mechanical Engineering",
        grade_or_marks="CGPA: 3.95",
        issue_date="2024",
    )

    result = verify_student_record(fields, db_session, institution_id=inst_id)

    assert result.record_found is True
    assert result.cgpa_match is False
    assert any("CGPA on certificate (3.95) contradicts" in d for d in result.discrepancies)


def test_tc_tmp_05_missing_student_record(db_session: Session):
    """TC-TMP-05: Missing student record returns record_found=False."""
    fields = CertificateFields(
        student_name="UNKNOWN STUDENT",
        register_number="NONEXISTENT-9999",
        course_degree="Physics",
    )

    result = verify_student_record(fields, db_session)

    assert result.record_found is False
    assert result.matched_record_id is None
    assert any("not found" in d for d in result.discrepancies)


def test_fuzzy_name_match_tolerates_minor_ocr_noise(db_session: Session):
    """Fuzzy matching allows minor OCR typos in name (e.g. middle initial missing)."""
    inst_id = str(uuid.uuid4())
    rec = InstitutionRecordModel(
        id=str(uuid.uuid4()),
        institution_id=inst_id,
        student_name="ROBERT BRUCE BANNER",
        roll_number="PH2020-0001",
        degree_name="Nuclear Physics",
        passing_year=2024,
        cgpa=4.0,
    )
    db_session.add(rec)
    db_session.commit()

    # OCR recognized without middle name: "Robert Banner"
    fields = CertificateFields(
        student_name="Robert Banner",
        register_number="PH2020-0001",
        course_degree="Nuclear Physics",
        grade_or_marks="4.0",
        issue_date="2024",
    )

    result = verify_student_record(fields, db_session, institution_id=inst_id)

    assert result.record_found is True
    assert result.name_match_score >= 0.70
