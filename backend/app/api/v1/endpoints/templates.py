import json
import uuid
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.template import InstitutionModel, InstitutionTemplateModel
from app.modules.template_matching.diagnostics import run_template_diagnostics
from app.modules.template_matching.registration_service import (
    register_institution_template,
)
from app.schemas.template_matching import (
    TemplateDetailResponse,
    TemplateSummary,
)

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get(
    "",
    response_model=List[TemplateSummary],
    status_code=status.HTTP_200_OK,
    summary="List registered institutional certificate templates",
)
def list_templates(
    institution_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[TemplateSummary]:
    """Retrieve list of registered institutional certificate templates."""
    query = db.query(
        InstitutionTemplateModel, InstitutionModel.name.label("institution_name")
    ).join(
        InstitutionModel,
        InstitutionTemplateModel.institution_id == InstitutionModel.id,
        isouter=True,
    )
    if institution_id:
        query = query.filter(InstitutionTemplateModel.institution_id == institution_id)

    results = query.all()
    summaries = []
    for tpl, inst_name in results:
        summaries.append(
            TemplateSummary(
                template_id=str(tpl.id),
                institution_id=str(tpl.institution_id),
                institution_name=inst_name or "Unknown Institution",
                template_name=tpl.template_name,
                degree_program=tpl.degree_program,
                uploaded_at=tpl.created_at,
            )
        )
    return summaries


@router.post(
    "",
    response_model=TemplateSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Register new institutional certificate template",
)
async def create_template(
    institution_name: str = Form(..., description="Issuing university or college name"),
    template_name: str = Form(..., description="Descriptive template name"),
    file: UploadFile = File(..., description="Master template image (PNG or JPG)"),
    institution_id: Optional[str] = Form(None, description="Optional existing institution UUID"),
    degree_program: Optional[str] = Form(None, description="Degree or program specification"),
    effective_year_start: Optional[int] = Form(None, description="Start year"),
    effective_year_end: Optional[int] = Form(None, description="End year"),
    seal_roi_json: Optional[str] = Form(None, description="JSON string of {x, y, width, height}"),
    variable_regions_json: Optional[str] = Form(
        None, description="JSON array of variable ROI rects"
    ),
    db: Session = Depends(get_db),
) -> TemplateSummary:
    """Upload and index reference master template with seal ROIs and variable text masks."""
    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # Decode image from buffer
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decode image. Ensure file is a valid JPG or PNG.",
        )

    # Resolve or create institution
    inst: Optional[InstitutionModel] = None
    if institution_id:
        inst = db.query(InstitutionModel).filter(InstitutionModel.id == institution_id).first()
    if not inst:
        inst = db.query(InstitutionModel).filter(InstitutionModel.name == institution_name).first()
    if not inst:
        inst = InstitutionModel(
            id=institution_id or str(uuid.uuid4()),
            name=institution_name,
        )
        db.add(inst)
        db.commit()
        db.refresh(inst)

    # Parse optional JSON ROIs
    seal_roi: Optional[Dict[str, Any]] = None
    if seal_roi_json:
        try:
            seal_roi = json.loads(seal_roi_json)
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="seal_roi_json must be valid JSON.",
            ) from err

    variable_regions: Optional[List[Dict[str, Any]]] = None
    if variable_regions_json:
        try:
            variable_regions = json.loads(variable_regions_json)
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="variable_regions_json must be valid JSON array.",
            ) from err

    tpl = register_institution_template(
        template_img=img,
        institution_id=str(inst.id),
        template_name=template_name,
        db=db,
        degree_program=degree_program,
        effective_year_start=effective_year_start,
        effective_year_end=effective_year_end,
        seal_roi=seal_roi,
        variable_regions=variable_regions,
    )

    return TemplateSummary(
        template_id=str(tpl.id),
        institution_id=str(inst.id),
        institution_name=inst.name,
        template_name=tpl.template_name,
        degree_program=tpl.degree_program,
        uploaded_at=tpl.created_at,
    )


@router.get(
    "/diagnostics",
    status_code=status.HTTP_200_OK,
    summary="Template subsystem diagnostics & health benchmarks",
)
def template_diagnostics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Run diagnostics on template storage, cached descriptors, and database latency."""
    return run_template_diagnostics(db)


@router.get(
    "/{template_id}",
    response_model=TemplateDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve detailed master template record",
)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
) -> TemplateDetailResponse:
    """Fetch registered template details by ID."""
    tpl = (
        db.query(InstitutionTemplateModel)
        .filter(InstitutionTemplateModel.id == template_id)
        .first()
    )
    if not tpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID '{template_id}' not found.",
        )

    inst = db.query(InstitutionModel).filter(InstitutionModel.id == tpl.institution_id).first()

    return TemplateDetailResponse(
        template_id=str(tpl.id),
        institution_id=str(tpl.institution_id),
        institution_name=inst.name if inst else "Unknown Institution",
        template_name=tpl.template_name,
        degree_program=tpl.degree_program,
        uploaded_at=tpl.created_at,
        image_path=tpl.image_path,
        seal_roi=tpl.seal_roi_json,
        variable_regions=tpl.variable_regions_json,
    )
