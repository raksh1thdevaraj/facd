"""Unit and integration tests for VisualCNNService and pipeline contract."""

import time
from pathlib import Path

from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.ml_prediction import MLPredictionModel
from app.modules.visual_model.service import VisualCNNService
from app.schemas.pipeline import MLInferenceOutput
from app.schemas.visual_prediction import VisualPredictionResult


def test_visual_service_prediction_and_contract(tmp_path: Path):
    """Verify end-to-end prediction, DTO schema, and conversion to SPEC-02 output."""
    test_img = tmp_path / "cert_test.png"
    Image.new("RGB", (512, 512), color=(250, 248, 245)).save(test_img)

    service = VisualCNNService(device="cpu")
    result = service.predict(
        image_path=test_img,
        certificate_id="cert-12345",
        generate_gradcam=True,
        output_dir=tmp_path / "reports",
    )

    assert isinstance(result, VisualPredictionResult)
    assert result.certificate_id == "cert-12345"
    assert result.model_type == "cnn_visual"
    assert 0.0 <= result.manipulation_probability <= 1.0
    assert result.predicted_class in ("genuine", "manipulated")
    assert len(result.visual_embedding) == 512
    assert result.gradcam_heatmap_path is not None
    assert Path(result.gradcam_heatmap_path).exists()

    # Convert to canonical SPEC-02 contract
    spec_output = result.to_pipeline_output()
    assert isinstance(spec_output, MLInferenceOutput)
    assert spec_output.model_type == "cnn_visual"
    assert spec_output.predicted_class == result.predicted_class
    assert spec_output.gradcam_heatmap_path == result.gradcam_heatmap_path


def test_visual_service_latency_benchmark(tmp_path: Path):
    """Verify single image inference on CPU meets latency specification (< 500ms)."""
    test_img = tmp_path / "bench_cert.png"
    Image.new("RGB", (512, 512), color=(255, 255, 255)).save(test_img)

    service = VisualCNNService(device="cpu")

    # Warmup
    _ = service.predict(image_path=test_img, generate_gradcam=False)

    # Measured run
    t0 = time.perf_counter()
    res = service.predict(image_path=test_img, generate_gradcam=False)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert elapsed_ms < 500.0, f"CPU latency {elapsed_ms:.2f}ms exceeded 500ms specification"
    assert res.latency_ms > 0.0


def test_visual_service_db_persistence(tmp_path: Path):
    """Verify prediction result persists to SQLite database."""
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    test_img = tmp_path / "db_cert.png"
    Image.new("RGB", (512, 512), color=(220, 220, 220)).save(test_img)

    service = VisualCNNService(device="cpu")
    result = service.predict(
        image_path=test_img,
        certificate_id="db-cert-999",
        generate_gradcam=False,
        db_session=session,
    )

    saved_row = session.query(MLPredictionModel).filter_by(certificate_id="db-cert-999").first()
    assert saved_row is not None
    assert saved_row.model_type == "cnn_visual"
    assert saved_row.predicted_class == result.predicted_class
    session.close()
