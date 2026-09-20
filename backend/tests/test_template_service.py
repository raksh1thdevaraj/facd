import uuid

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.models.record import InstitutionRecordModel
from app.models.template import (
    InstitutionModel,
    TemplateMatchResultModel,
)
from app.modules.template_matching.registration_service import (
    register_institution_template,
)
from app.modules.template_matching.service import TemplateVerificationService
from app.schemas.pipeline import CertificateFields
from app.schemas.template_matching import TierStatus


def _create_synthetic_certificate(
    student_name: str = "Alice Doe",
    inst_name: str = "Stanford University",
    degree: str = "Bachelor of Science",
) -> np.ndarray:
    img = np.ones((700, 900, 3), dtype=np.uint8) * 255
    cv2.rectangle(img, (20, 20), (880, 680), (30, 30, 30), 4)
    cv2.circle(img, (450, 120), 40, (0, 100, 200), -1)
    cv2.putText(img, inst_name, (250, 220), cv2.FONT_HERSHEY_TRIPLEX, 0.9, (0, 0, 0), 2)
    cv2.putText(
        img, f"Presented to {student_name}", (250, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2
    )
    cv2.putText(img, f"Degree of {degree}", (260, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    cv2.putText(
        img, "Graduation Year: 2024", (300, 520), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2
    )
    return img


def test_service_tier_1_verified(db_session: Session):
    """End-to-end: Registered template + authentic database record -> Tier 1 Verified."""
    inst = InstitutionModel(id=str(uuid.uuid4()), name="Stanford University")
    db_session.add(inst)
    db_session.commit()

    master_img = _create_synthetic_certificate()
    template = register_institution_template(
        template_img=master_img,
        institution_id=str(inst.id),
        template_name="Stanford Official BS",
        db=db_session,
        degree_program="Bachelor of Science",
        seal_roi={"x": 410, "y": 80, "width": 80, "height": 80},
    )

    rec = InstitutionRecordModel(
        id=str(uuid.uuid4()),
        institution_id=str(inst.id),
        student_name="ALICE DOE",
        roll_number="STAN-2020-01",
        degree_name="Bachelor of Science",
        passing_year=2024,
        cgpa=3.90,
    )
    db_session.add(rec)
    db_session.commit()

    service = TemplateVerificationService()
    fields = CertificateFields(
        student_name="Alice Doe",
        register_number="STAN-2020-01",
        institution_name="Stanford University",
        course_degree="Bachelor of Science",
        grade_or_marks="3.90",
        issue_date="2024",
    )

    cert_id = str(uuid.uuid4())
    result = service.verify(
        query_img=master_img,
        extracted_fields=fields,
        db=db_session,
        document_id=str(uuid.uuid4()),
        certificate_id=cert_id,
        template_id=str(template.id),
        institution_id=str(inst.id),
    )

    assert result.tier_classification.tier == TierStatus.TIER_1_VERIFIED
    assert result.template_metrics is not None
    assert result.template_metrics.ssim_score >= 0.85
    assert result.template_metrics.alignment_success is True
    assert result.record_result.record_found is True

    # Test conversion to SPEC-02 TemplateMatchOutput
    pipeline_out = result.to_pipeline_output()
    assert pipeline_out.matched_template_id == str(template.id)
    assert pipeline_out.layout_similarity_score is not None
    assert pipeline_out.layout_similarity_score >= 0.85
    assert pipeline_out.record_found is True
    assert pipeline_out.template_risk_score == 0.0

    # Verify DB persistence
    saved_result = (
        db_session.query(TemplateMatchResultModel).filter_by(certificate_id=cert_id).first()
    )
    assert saved_result is not None
    assert saved_result.tier_status == TierStatus.TIER_1_VERIFIED.value


def test_service_graceful_fallback_no_template_no_record(db_session: Session):
    """FR-TPL-04: Graceful execution when neither template nor record is registered."""
    service = TemplateVerificationService()
    fields = CertificateFields(
        student_name="UNKNOWN PERSON",
        register_number="UNREGISTERED-123",
        institution_name="UNREGISTERED UNIVERSITY",
    )

    result = service.verify(
        query_img=np.ones((400, 400, 3), dtype=np.uint8) * 255,
        extracted_fields=fields,
        db=db_session,
        document_id=str(uuid.uuid4()),
    )

    assert result.tier_classification.tier == TierStatus.TIER_3_UNVERIFIED
    assert result.template_metrics is None
    assert result.record_result.record_found is False

    # SPEC-02 output still valid
    pipeline_out = result.to_pipeline_output()
    assert pipeline_out.matched_template_id is None
    assert pipeline_out.record_found is False
    assert pipeline_out.template_risk_score == 50.0
