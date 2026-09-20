import csv
import io
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.record import InstitutionRecordModel
from app.schemas.template_matching import RecordBulkImportResponse


def _find_column(header: List[str], candidate_names: List[str]) -> Optional[int]:
    """Find index of column matching one of candidate names (case-insensitive)."""
    norm_header = [h.strip().lower().replace(" ", "_") for h in header]
    for cand in candidate_names:
        if cand in norm_header:
            return norm_header.index(cand)
    return None


def import_records_from_csv(
    csv_content: str,
    institution_id: str,
    db: Session,
) -> RecordBulkImportResponse:
    """Parse and bulk-import institutional student graduation records from CSV content.

    Args:
        csv_content: Raw string content of the uploaded CSV file.
        institution_id: UUID of the academic institution owning these records.
        db: SQLAlchemy database session.

    Returns:
        RecordBulkImportResponse summarizing inserted records, duplicates, and errors.
    """
    reader = csv.reader(io.StringIO(csv_content.strip()))
    rows = list(reader)

    if not rows or len(rows) < 2:
        return RecordBulkImportResponse(
            total_records_processed=0,
            records_inserted=0,
            duplicates_skipped=0,
            errors=["CSV file is empty or missing data rows."],
        )

    header = rows[0]
    idx_name = _find_column(header, ["student_name", "name", "candidate_name", "student"])
    idx_roll = _find_column(
        header, ["roll_number", "roll_no", "register_number", "reg_no", "rollno", "regno"]
    )
    idx_degree = _find_column(
        header, ["degree_name", "degree", "course_degree", "course", "program"]
    )
    idx_year = _find_column(header, ["passing_year", "year", "graduation_year", "pass_year"])
    idx_cgpa = _find_column(header, ["cgpa", "gpa", "marks", "cgpa_or_marks", "score"])
    idx_date = _find_column(header, ["issue_date", "date", "issued_on"])

    if idx_name is None or idx_roll is None or idx_degree is None or idx_year is None:
        missing = []
        if idx_name is None:
            missing.append("student_name")
        if idx_roll is None:
            missing.append("roll_number")
        if idx_degree is None:
            missing.append("degree_name")
        if idx_year is None:
            missing.append("passing_year")
        return RecordBulkImportResponse(
            total_records_processed=0,
            records_inserted=0,
            duplicates_skipped=0,
            errors=[f"Required CSV columns missing: {', '.join(missing)}."],
        )

    # Fetch existing roll numbers for this institution to avoid duplicates
    existing_rolls = {
        r[0].strip().upper()
        for r in db.query(InstitutionRecordModel.roll_number)
        .filter(InstitutionRecordModel.institution_id == institution_id)
        .all()
    }

    records_to_insert: List[InstitutionRecordModel] = []
    duplicates_skipped = 0
    errors: List[str] = []

    for row_num, row in enumerate(rows[1:], start=2):
        if not row or all(c.strip() == "" for c in row):
            continue

        try:
            name = row[idx_name].strip()
            roll = row[idx_roll].strip().upper()
            degree = row[idx_degree].strip()
            year_str = row[idx_year].strip()

            if not name or not roll:
                errors.append(f"Row {row_num}: Student name or roll number is empty.")
                continue

            try:
                year = int(year_str)
            except ValueError:
                errors.append(f"Row {row_num}: Invalid passing year '{year_str}'.")
                continue

            cgpa_val = None
            if idx_cgpa is not None and idx_cgpa < len(row) and row[idx_cgpa].strip():
                try:
                    cgpa_val = float(row[idx_cgpa].strip())
                except ValueError:
                    pass

            date_val = None
            if idx_date is not None and idx_date < len(row) and row[idx_date].strip():
                date_val = row[idx_date].strip()

            if roll in existing_rolls:
                duplicates_skipped += 1
                continue

            existing_rolls.add(roll)
            new_record = InstitutionRecordModel(
                institution_id=institution_id,
                student_name=name,
                roll_number=roll,
                degree_name=degree,
                passing_year=year,
                cgpa=cgpa_val,
                issue_date=date_val,
            )
            records_to_insert.append(new_record)

        except Exception as e:
            errors.append(f"Row {row_num}: Error processing record — {str(e)}")

    if records_to_insert:
        db.bulk_save_objects(records_to_insert)
        db.commit()

    return RecordBulkImportResponse(
        total_records_processed=len(rows) - 1,
        records_inserted=len(records_to_insert),
        duplicates_skipped=duplicates_skipped,
        errors=errors[:20],  # Return up to 20 errors
    )
