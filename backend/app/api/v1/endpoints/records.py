import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.record import InstitutionRecordModel
from app.modules.template_matching.record_importer import import_records_from_csv
from app.schemas.template_matching import (
    RecordBulkImportResponse,
    RecordCreateRequest,
)

router = APIRouter(prefix="/records", tags=["Records"])


@router.post(
    "/bulk-import",
    response_model=RecordBulkImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk import student graduation records via CSV",
)
async def bulk_import_records(
    institution_id: str = Form(..., description="UUID of academic institution"),
    file: UploadFile = File(..., description="CSV file with student records"),
    db: Session = Depends(get_db),
) -> RecordBulkImportResponse:
    """Import student records from CSV file with column validation and deduplication."""
    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded CSV file is empty.",
        )

    try:
        csv_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content_bytes.decode("latin-1")

    return import_records_from_csv(
        csv_content=csv_text,
        institution_id=institution_id,
        db=db,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a single student graduation record",
)
def create_record(
    payload: RecordCreateRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Manually add an individual authentic student record."""
    clean_roll = payload.roll_number.strip().upper()
    existing = (
        db.query(InstitutionRecordModel)
        .filter(
            InstitutionRecordModel.institution_id == payload.institution_id,
            InstitutionRecordModel.roll_number == clean_roll,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Record with roll number '{clean_roll}' already exists for this institution.",
        )

    rec = InstitutionRecordModel(
        id=str(uuid.uuid4()),
        institution_id=payload.institution_id,
        student_name=payload.student_name.strip(),
        roll_number=clean_roll,
        degree_name=payload.degree_name.strip(),
        passing_year=payload.passing_year,
        cgpa=payload.cgpa,
        issue_date=payload.issue_date,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "id": str(rec.id),
        "student_name": rec.student_name,
        "roll_number": rec.roll_number,
        "degree_name": rec.degree_name,
        "passing_year": rec.passing_year,
        "cgpa": rec.cgpa,
        "created_at": rec.created_at.isoformat(),
    }


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Query institutional records by roll number or institution",
)
def list_records(
    institution_id: Optional[str] = None,
    roll_number: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Search registered student records."""
    query = db.query(InstitutionRecordModel)
    if institution_id:
        query = query.filter(InstitutionRecordModel.institution_id == institution_id)
    if roll_number:
        query = query.filter(InstitutionRecordModel.roll_number == roll_number.strip().upper())

    records = query.limit(100).all()
    return [
        {
            "id": str(r.id),
            "institution_id": str(r.institution_id),
            "student_name": r.student_name,
            "roll_number": r.roll_number,
            "degree_name": r.degree_name,
            "passing_year": r.passing_year,
            "cgpa": r.cgpa,
            "issue_date": r.issue_date,
        }
        for r in records
    ]
