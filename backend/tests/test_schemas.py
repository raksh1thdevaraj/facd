import pytest
from pydantic import ValidationError

from app.schemas.pipeline import (
    CertificateFields,
    ConsistencyCheckItem,
    ContributingFactor,
    ForensicsOutput,
    IngestionOutput,
    MLInferenceOutput,
    TextConsistencyOutput,
    VerificationReportDTO,
)
from app.schemas.primitives import (
    BoundingBox,
    CheckStatus,
    PixelBoundingBox,
    RiskBand,
)


def test_bounding_box_validation() -> None:
    """Verify normalized bounding box coordinates must be 0.0 to 1.0."""
    valid_box = BoundingBox(x1=0.1, y1=0.2, x2=0.8, y2=0.9)
    assert valid_box.x1 == 0.1
    assert valid_box.x2 == 0.8

    with pytest.raises(ValidationError):
        BoundingBox(x1=-0.1, y1=0.2, x2=0.8, y2=0.9)

    with pytest.raises(ValidationError):
        BoundingBox(x1=0.1, y1=0.2, x2=1.5, y2=0.9)


def test_pixel_bounding_box_validation() -> None:
    """Verify absolute pixel coordinates."""
    valid_box = PixelBoundingBox(x=10, y=20, width=100, height=50)
    assert valid_box.width == 100

    with pytest.raises(ValidationError):
        PixelBoundingBox(x=-1, y=20, width=100, height=50)

    with pytest.raises(ValidationError):
        PixelBoundingBox(x=10, y=20, width=0, height=50)


def test_ingestion_output_model() -> None:
    """Verify IngestionOutput instantiation."""
    output = IngestionOutput(
        document_id="123e4567-e89b-12d3-a456-426614174000",
        original_filename="sample_cert.pdf",
        file_extension=".pdf",
        mime_type="application/pdf",
        file_size_bytes=1048576,
        raw_storage_path="./storage/uploads/sample_cert.pdf",
        is_pdf=True,
        page_count=1,
    )
    assert output.is_pdf is True
    assert output.file_extension == ".pdf"


def test_score_fusion_and_verification_report_dto() -> None:
    """Verify full Report DTO model composition and validation."""
    fields = CertificateFields(
        student_name="Jane Doe",
        student_name_confidence=0.95,
        register_number="REG2026001",
        register_number_confidence=0.92,
        institution_name="Global Tech University",
        institution_name_confidence=0.98,
        course_degree="Bachelor of Science in Computer Science",
        course_degree_confidence=0.94,
        grade_or_marks="First Class with Distinction",
        grade_or_marks_confidence=0.91,
        issue_date="2026-05-15",
        issue_date_confidence=0.90,
        certificate_number="CERT-998822",
        certificate_number_confidence=0.96,
    )

    consistency = TextConsistencyOutput(
        document_id="doc-123",
        overall_status=CheckStatus.PASSED,
        consistency_risk_score=5.0,
        checks=[
            ConsistencyCheckItem(
                rule_id="RULE_DATE_LOGIC",
                name="Graduation Date Validation",
                status=CheckStatus.PASSED,
                confidence=1.0,
                details="Issue date is chronologically valid.",
                field_affected="issue_date",
            )
        ],
    )

    forensics = ForensicsOutput(
        document_id="doc-123",
        ela_heatmap_path="./storage/reports/ela_heatmap.png",
        ela_score=0.08,
        copy_move_detected=False,
        copy_move_clusters_count=0,
        copy_move_score=0.02,
        font_irregularity_score=0.05,
        noise_inconsistency_score=0.04,
        forensics_risk_score=8.5,
        suspicious_regions=[],
    )

    ml = MLInferenceOutput(
        model_version="v1.0",
        model_type="tabular_baseline",
        manipulation_probability=0.06,
        predicted_class="genuine",
        feature_contributions={"ela_score": 0.02, "ocr_confidence": -0.05},
    )

    factor = ContributingFactor(
        factor_id="F1",
        category="OCR",
        impact="LOW",
        weight_percentage=20.0,
        description="High OCR token confidence across all fields.",
    )

    report = VerificationReportDTO(
        verification_id="verif-777",
        document_id="doc-123",
        timestamp="2026-09-18T10:00:00Z",
        verifier_username="officer1",
        risk_score=6.2,
        risk_band=RiskBand.LOW,
        extracted_fields=fields,
        consistency_results=consistency,
        forensics_results=forensics,
        ml_results=ml,
        contributing_factors=[factor],
        summary_verdict="Certificate appears authentic with low risk indicators.",
    )

    assert report.risk_band == RiskBand.LOW
    assert report.extracted_fields.student_name == "Jane Doe"
    assert len(report.contributing_factors) == 1


def test_text_consistency_schemas_and_db_model() -> None:
    """Verify TextConsistencyResult and TextConsistencyModel initialization and conversion."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database import Base
    from app.models.text_consistency import TextConsistencyModel
    from app.schemas.text_consistency import (
        AnomalousRegion,
        AnomalyType,
        TextConsistencyResult,
    )

    region = AnomalousRegion(
        anomaly_type=AnomalyType.BASELINE_DRIFT,
        severity=0.75,
        description="Raised baseline",
        bbox=BoundingBox(x1=0.1, y1=0.1, x2=0.2, y2=0.2),
        pixel_bbox=PixelBoundingBox(x=10, y=10, width=50, height=20),
        token_text="Spliced",
    )

    result = TextConsistencyResult(
        document_id="test-doc-99",
        overall_text_consistency_score=0.78,
        baseline_alignment_score=0.70,
        font_size_consistency_score=0.90,
        stroke_weight_consistency_score=0.85,
        spacing_consistency_score=0.92,
        format_consistency_score=1.0,
        logical_consistency_score=0.80,
        anomalous_regions=[region],
    )

    assert result.status == CheckStatus.WARNING
    assert result.consistency_risk_score == 22.0

    pipeline_output = result.to_pipeline_output()
    assert pipeline_output.overall_status == CheckStatus.WARNING
    assert pipeline_output.consistency_risk_score == 22.0

    # Test SQLAlchemy database table creation
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    session_cls = sessionmaker(bind=test_engine)
    session = session_cls()

    db_record = TextConsistencyModel(
        certificate_id="cert-123",
        overall_score=result.overall_text_consistency_score,
        baseline_score=result.baseline_alignment_score,
        font_size_score=result.font_size_consistency_score,
        stroke_weight_score=result.stroke_weight_consistency_score,
        spacing_score=result.spacing_consistency_score,
        format_score=result.format_consistency_score,
        logical_score=result.logical_consistency_score,
        anomalous_regions_json=[region.model_dump()],
        visualization_image_path="/path/to/overlay.png",
    )
    session.add(db_record)
    session.commit()

    saved = session.query(TextConsistencyModel).filter_by(certificate_id="cert-123").first()
    assert saved is not None
    assert saved.overall_score == 0.78
    assert len(saved.anomalous_regions_json) == 1
    session.close()


def test_forensic_schemas_and_db_model() -> None:
    """Verify ForensicAnalysisResult and ForensicFindingModel persistence."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database import Base
    from app.models.forensic import ForensicFindingModel
    from app.schemas.forensics import CloneMatch, ForensicAnalysisResult
    from app.schemas.pipeline import SuspiciousRegion

    clone = CloneMatch(
        source_bbox=BoundingBox(x1=0.1, y1=0.1, x2=0.2, y2=0.2),
        target_bbox=BoundingBox(x1=0.5, y1=0.5, x2=0.6, y2=0.6),
        source_pixel_bbox=PixelBoundingBox(x=50, y=50, width=50, height=50),
        target_pixel_bbox=PixelBoundingBox(x=250, y=250, width=50, height=50),
        inlier_count=8,
        confidence=0.90,
        displacement_vector=(200.0, 200.0),
    )

    suspicious = SuspiciousRegion(
        region_id="reg-clone-1",
        bbox=clone.target_bbox,
        pixel_bbox=clone.target_pixel_bbox,
        forensic_type="COPY_MOVE",
        anomaly_score=0.90,
        description="Cloned stamp patch",
    )

    result = ForensicAnalysisResult(
        document_id="doc-forensic-99",
        overall_forensic_score=0.45,
        ela_score=0.88,
        copy_move_score=0.30,
        noise_inconsistency_score=0.92,
        detected_clones=[clone],
        suspicious_regions=[suspicious],
        heatmap_image_path="/storage/reports/doc99_heatmap.png",
    )

    assert result.forensics_risk_score == 55.0
    pipeline_out = result.to_pipeline_output()
    assert pipeline_out.copy_move_detected is True
    assert pipeline_out.copy_move_clusters_count == 1
    assert pipeline_out.forensics_risk_score == 55.0

    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    session_cls = sessionmaker(bind=test_engine)
    session = session_cls()

    finding = ForensicFindingModel(
        certificate_id="cert-99",
        finding_type="COPY_MOVE_CLONE",
        confidence_score=0.90,
        bounding_box_json=clone.target_bbox.model_dump(),
        description="Cloned stamp detected via SIFT/RANSAC",
        heatmap_image_path=result.heatmap_image_path,
    )
    session.add(finding)
    session.commit()

    saved = session.query(ForensicFindingModel).filter_by(certificate_id="cert-99").first()
    assert saved is not None
    assert saved.finding_type == "COPY_MOVE_CLONE"
    assert saved.confidence_score == 0.90
    session.close()
