import re
from typing import Optional

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.models.record import InstitutionRecordModel
from app.schemas.pipeline import CertificateFields
from app.schemas.template_matching import RecordVerificationResult


def _extract_year_from_text(text: Optional[str]) -> Optional[int]:
    """Extract a 4-digit year (1950-2099) from date or general text."""
    if not text:
        return None
    matches = re.findall(r"\b(19\d\d|20\d\d)\b", text)
    if matches:
        return int(matches[-1])  # Take the last mentioned year (typically graduation/issue)
    return None


def _extract_numeric_cgpa(grade_or_marks: Optional[str]) -> Optional[float]:
    """Extract numeric GPA/CGPA or percentage from grade string."""
    if not grade_or_marks:
        return None
    # Look for patterns like "8.75", "CGPA: 9.1", "3.85 / 4.0"
    match = re.search(r"(\d{1,2}(?:\.\d{1,3})?)", grade_or_marks)
    if match:
        try:
            val = float(match.group(1))
            return val
        except ValueError:
            return None
    return None


def verify_student_record(
    extracted_fields: CertificateFields,
    db: Session,
    institution_id: Optional[str] = None,
) -> RecordVerificationResult:
    """Query institutional records database and cross-verify extracted student particulars.

    Args:
        extracted_fields: Structured OCR-extracted certificate fields.
        db: SQLAlchemy database session.
        institution_id: Optional UUID of institution to restrict search.

    Returns:
        RecordVerificationResult with field matches, fuzzy scores, and discrepancy findings.
    """
    roll_no = extracted_fields.register_number or extracted_fields.certificate_number
    cert_name = (extracted_fields.student_name or "").strip()
    discrepancies = []

    db_record: Optional[InstitutionRecordModel] = None

    # 1. Primary Lookup: Exact or normalized Roll / Registration Number
    if roll_no:
        clean_roll = roll_no.strip().upper()
        query = db.query(InstitutionRecordModel)
        if institution_id:
            query = query.filter(InstitutionRecordModel.institution_id == institution_id)

        # Try exact match first
        db_record = query.filter(InstitutionRecordModel.roll_number == clean_roll).first()

        # If not found, try case-insensitive or stripped alphanumeric match
        if not db_record:
            all_records = query.all()
            for rec in all_records:
                if rec.roll_number.strip().upper() == clean_roll:
                    db_record = rec
                    break

    # 2. Fallback Lookup: High-confidence student name match if roll number is missing
    if not db_record and cert_name and len(cert_name) >= 3:
        query = db.query(InstitutionRecordModel)
        if institution_id:
            query = query.filter(InstitutionRecordModel.institution_id == institution_id)
        candidates = query.all()

        best_cand = None
        best_ratio = 0.0
        for cand in candidates:
            ratio = fuzz.token_sort_ratio(cert_name.lower(), cand.student_name.lower())
            if ratio > best_ratio:
                best_ratio = ratio
                best_cand = cand

        if best_ratio >= 90.0 and best_cand:
            db_record = best_cand

    # If no record exists in database
    if not db_record:
        return RecordVerificationResult(
            record_found=False,
            matched_record_id=None,
            name_match_score=0.0,
            roll_no_match=False,
            degree_match=False,
            passing_year_match=False,
            cgpa_match=False,
            discrepancies=["Student record not found in institutional database."],
        )

    # 3. Cross-Verify Individual Particulars
    # A. Student Name Verification (Token Sort Fuzzy Match)
    name_score = 0.0
    name_match = False
    if cert_name:
        ratio = fuzz.token_sort_ratio(cert_name.lower(), db_record.student_name.lower())
        name_score = round(ratio / 100.0, 4)
        name_match = ratio >= 85.0
        if ratio < 60.0:
            discrepancies.append(
                f"Name on certificate ('{cert_name}') does not match university record "
                f"('{db_record.student_name}') registered for roll number {db_record.roll_number}."
            )
        elif not name_match:
            discrepancies.append(
                f"Name on certificate ('{cert_name}') differs slightly from database record "
                f"('{db_record.student_name}') (similarity {ratio}%)."
            )
    else:
        discrepancies.append("Student name missing from extracted certificate text.")

    # B. Roll Number Match
    roll_match = False
    if roll_no:
        clean_extracted_roll = roll_no.strip().upper()
        clean_db_roll = db_record.roll_number.strip().upper()
        roll_match = clean_extracted_roll == clean_db_roll
        if not roll_match:
            discrepancies.append(
                f"Roll number mismatch: certificate '{roll_no}' "
                f"vs record '{db_record.roll_number}'."
            )
    else:
        discrepancies.append("Roll number missing from extracted certificate text.")

    # C. Degree Program Match
    degree_match = True
    if extracted_fields.course_degree and db_record.degree_name:
        deg_ratio = fuzz.token_sort_ratio(
            extracted_fields.course_degree.lower(), db_record.degree_name.lower()
        )
        degree_match = deg_ratio >= 75.0
        if not degree_match:
            discrepancies.append(
                f"Degree mismatch: certificate specifies '{extracted_fields.course_degree}' "
                f"but university record states '{db_record.degree_name}'."
            )

    # D. Passing Year Match
    passing_year_match = True
    extracted_year = _extract_year_from_text(extracted_fields.issue_date)
    if extracted_year and db_record.passing_year:
        passing_year_match = extracted_year == db_record.passing_year
        if not passing_year_match:
            discrepancies.append(
                f"Passing year on certificate ({extracted_year}) contradicts "
                f"institutional record ({db_record.passing_year})."
            )

    # E. CGPA / Marks Match
    cgpa_match = True
    extracted_cgpa = _extract_numeric_cgpa(extracted_fields.grade_or_marks)
    if extracted_cgpa is not None and db_record.cgpa is not None:
        cgpa_diff = abs(extracted_cgpa - db_record.cgpa)
        cgpa_match = cgpa_diff <= 0.05
        if not cgpa_match:
            discrepancies.append(
                f"CGPA on certificate ({extracted_cgpa}) contradicts "
                f"institutional record ({db_record.cgpa})."
            )

    return RecordVerificationResult(
        record_found=True,
        matched_record_id=str(db_record.id),
        name_match_score=name_score,
        roll_no_match=roll_match,
        degree_match=degree_match,
        passing_year_match=passing_year_match,
        cgpa_match=cgpa_match,
        discrepancies=discrepancies,
    )
