"""Unit and integration tests for BaselineMLService (Phase 09).

Tests end-to-end orchestration, DB persistence in ml_predictions table,
and canonical SPEC-02 MLInferenceOutput contract compliance.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.ml_prediction import MLPredictionModel
from app.modules.ml_classifier.service import BaselineMLService
from app.schemas.pipeline import MLInferenceOutput


@pytest.fixture
def db_session():
    """In-memory SQLite test database fixture."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def test_classify_certificate_end_to_end(db_session):
    """Verify service extracts features, infers probability, calculates local explanations,

    and saves to database.
    """
    service = BaselineMLService()

    mock_forensics = {
        "ela_score": 0.35,  # Low score indicates manipulation
        "copy_move_score": 0.40,
        "cloned_regions_count": 2,
        "noise_inconsistency_score": 0.50,
    }
    mock_ocr = {
        "mean_confidence": 0.72,
        "min_confidence": 0.45,
        "flagged_fields": ["student_name", "cgpa"],
        "missing_critical_fields": ["degree"],
    }

    result = service.classify_certificate(
        certificate_id="cert-test-uuid-1234",
        forensics_result=mock_forensics,
        ocr_result=mock_ocr,
        db_session=db_session,
    )

    assert result.certificate_id == "cert-test-uuid-1234"
    assert 0.0 <= result.manipulation_probability <= 1.0
    assert result.predicted_class in ["authentic", "manipulated"]
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.feature_contributions) == 5
    assert result.latency_ms > 0.0
    assert result.model_version == "1.0.0"

    # Verify DB persistence
    db_record = (
        db_session.query(MLPredictionModel)
        .filter(MLPredictionModel.certificate_id == "cert-test-uuid-1234")
        .first()
    )
    assert db_record is not None
    assert db_record.certificate_id == "cert-test-uuid-1234"
    assert db_record.predicted_class == result.predicted_class
    assert isinstance(db_record.feature_vector_json, dict)
    assert len(db_record.feature_vector_json) == 22
    assert len(db_record.feature_contributions_json) == 5


def test_get_pipeline_output_spec_02_contract():
    """Verify service produces canonical SPEC-02 MLInferenceOutput data contract."""
    service = BaselineMLService()

    output = service.get_pipeline_output(
        certificate_id="cert-spec-02-check",
    )

    assert isinstance(output, MLInferenceOutput)
    assert output.model_version == "1.0.0"
    assert output.predicted_class in ["authentic", "manipulated"]
    assert isinstance(output.feature_contributions, dict)
    assert len(output.feature_contributions) > 0

    # Validate dictionary export conforming to pipeline contract
    dumped = output.model_dump()
    assert "model_version" in dumped
    assert "model_type" in dumped
    assert "manipulation_probability" in dumped
    assert "predicted_class" in dumped
    assert "feature_contributions" in dumped
