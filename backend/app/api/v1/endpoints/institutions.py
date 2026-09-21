"""FastAPI router for university onboarding, template registration, and bulk records."""

from __future__ import annotations

import csv
import io
import math
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.record import InstitutionRecordModel
from app.models.template import InstitutionModel, InstitutionTemplateModel
from app.schemas.institution import (
    BulkRecordImportResponse,
    InstitutionCreate,
    InstitutionPaginatedList,
    InstitutionResponse,
)
from app.services.audit_service import AuditService

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.post(
    "",
    response_model=InstitutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new university or academic institution",
)
def register_institution(
    request: Request,
    payload: InstitutionCreate,
    db: Session = Depends(get_db),
) -> InstitutionResponse:
    existing = db.query(InstitutionModel).filter_by(code=payload.code.upper()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Institution with code '{payload.code}' already exists.",
        )

    inst = InstitutionModel(
        id=str(uuid.uuid4()),
        name=payload.name,
        code=payload.code.upper(),
        contact_email=payload.contact_email,
        is_active=True,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)

    client_ip = request.client.host if request.client else "127.0.0.1"
    AuditService.log_action(
        db=db,
        action="INSTITUTION_REGISTERED",
        ip_address=client_ip,
        details={"institution_id": inst.id, "name": inst.name, "code": inst.code},
    )

    return InstitutionResponse(
        id=inst.id,
        name=inst.name,
        code=inst.code,
        contact_email=inst.contact_email,
        is_active=inst.is_active,
        template_count=0,
        record_count=0,
        created_at=inst.created_at,
    )


@router.get(
    "",
    response_model=InstitutionPaginatedList,
    summary="List registered universities with pagination",
)
def list_institutions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> InstitutionPaginatedList:
    query = db.query(InstitutionModel)
    total = query.count()
    offset = (page - 1) * limit
    insts = query.order_by(desc(InstitutionModel.created_at)).offset(offset).limit(limit).all()

    items: list[InstitutionResponse] = []
    for inst in insts:
        t_count = db.query(InstitutionTemplateModel).filter_by(institution_id=inst.id).count()
        r_count = db.query(InstitutionRecordModel).filter_by(institution_id=inst.id).count()
        items.append(
            InstitutionResponse(
                id=inst.id,
                name=inst.name,
                code=inst.code,
                contact_email=inst.contact_email,
                is_active=inst.is_active,
                template_count=t_count,
                record_count=r_count,
                created_at=inst.created_at,
            )
        )

    total_pages = max(1, math.ceil(total / limit))
    return InstitutionPaginatedList(
        items=items, total=total, page=page, limit=limit, total_pages=total_pages
    )


@router.get(
    "/{institution_id}",
    response_model=InstitutionResponse,
    summary="Get details of a specific university",
)
def get_institution(institution_id: str, db: Session = Depends(get_db)) -> InstitutionResponse:
    inst = db.query(InstitutionModel).filter_by(id=institution_id).first()
    if inst is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution '{institution_id}' not found.",
        )

    t_count = db.query(InstitutionTemplateModel).filter_by(institution_id=inst.id).count()
    r_count = db.query(InstitutionRecordModel).filter_by(institution_id=inst.id).count()

    return InstitutionResponse(
        id=inst.id,
        name=inst.name,
        code=inst.code,
        contact_email=inst.contact_email,
        is_active=inst.is_active,
        template_count=t_count,
        record_count=r_count,
        created_at=inst.created_at,
    )


@router.post(
    "/{institution_id}/records/bulk",
    response_model=BulkRecordImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk import authorized student records from CSV",
)
async def bulk_import_records(
    institution_id: str,
    file: UploadFile = File(..., description="CSV file with student records"),
    db: Session = Depends(get_db),
) -> BulkRecordImportResponse:
    inst = db.query(InstitutionModel).filter_by(id=institution_id).first()
    if inst is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution '{institution_id}' not found.",
        )

    content = await file.read()
    try:
        text_data = content.decode("utf-8")
    except UnicodeDecodeError:
        text_data = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text_data))
    count = 0

    for row in reader:
        # Standardize CSV column keys
        clean_row = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}
        roll = clean_row.get("roll_number") or clean_row.get("roll_no") or clean_row.get("reg_no")
        name = clean_row.get("student_name") or clean_row.get("name")
        degree = clean_row.get("degree_name") or clean_row.get("degree") or clean_row.get("course")

        if not roll or not name:
            continue

        year = (
            int(clean_row["passing_year"]) if clean_row.get("passing_year", "").isdigit() else 2024
        )
        is_float = clean_row.get("cgpa", "").replace(".", "", 1).isdigit()
        cgpa = float(clean_row["cgpa"]) if is_float else None

        rec = InstitutionRecordModel(
            id=str(uuid.uuid4()),
            institution_id=institution_id,
            student_name=name,
            roll_number=roll,
            degree_name=degree or "Bachelor of Science",
            passing_year=year,
            cgpa=cgpa,
        )
        db.add(rec)
        count += 1

    db.commit()

    return BulkRecordImportResponse(
        institution_id=institution_id,
        imported_count=count,
        status="SUCCESS",
        message=f"Successfully imported {count} student records for institution '{inst.name}'.",
    )
