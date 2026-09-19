import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.modules.forensics.score_calculator import ForensicScoreCalculator
from app.modules.forensics.service import (
    ForensicService,
    get_forensic_service,
)
from app.schemas.forensics import CloneMatch, ForensicAnalysisResult, ForensicConfig
from app.schemas.pipeline import ForensicsOutput
from app.schemas.primitives import BoundingBox, PixelBoundingBox


def test_forensic_composite_score_bounds():
    """TC-FOR-04: Test composite scoring formula, bounds [0.0, 1.0], and veto penalties."""
    config = ForensicConfig(
        weight_ela=0.35,
        weight_copy_move=0.40,
        weight_noise=0.25,
    )
    calculator = ForensicScoreCalculator(config=config)

    # 1. Clean scores -> AUTHENTIC
    score, regions, cat = calculator.calculate(
        ela_score=1.0,
        copy_move_score=1.0,
        noise_score=1.0,
        ela_bboxes=[],
        clones=[],
        noise_bboxes=[],
    )
    assert score == 1.0
    assert cat == "AUTHENTIC"
    assert len(regions) == 0

    # 2. Veto penalty: copy-move clone with >= 8 inliers caps score at 0.30
    strong_clone = CloneMatch(
        source_bbox=BoundingBox(x1=0.1, y1=0.1, x2=0.2, y2=0.2),
        target_bbox=BoundingBox(x1=0.5, y1=0.5, x2=0.6, y2=0.6),
        source_pixel_bbox=PixelBoundingBox(x=50, y=50, width=50, height=50),
        target_pixel_bbox=PixelBoundingBox(x=250, y=250, width=50, height=50),
        inlier_count=10,
        confidence=0.95,
        displacement_vector=(200.0, 200.0),
    )

    score_veto, regions_veto, cat_veto = calculator.calculate(
        ela_score=0.95,
        copy_move_score=0.20,
        noise_score=0.95,
        ela_bboxes=[],
        clones=[strong_clone],
        noise_bboxes=[],
    )
    assert score_veto <= 0.30
    assert cat_veto == "MANIPULATED"
    assert len(regions_veto) == 1
    assert regions_veto[0].forensic_type == "COPY_MOVE"


def test_forensic_service_end_to_end_clean(tmp_path: Path):
    """Verify ForensicService runs end-to-end on clean image and creates heatmap."""
    service = ForensicService(report_dir=tmp_path)

    # Create uniform image saved as JPEG
    img = Image.new("RGB", (600, 800), color=(245, 245, 245))
    img_path = tmp_path / "clean_cert.jpg"
    img.save(img_path, format="JPEG", quality=90)

    result = service.analyze(
        document_id="doc_clean_forensic_01",
        raw_image_or_path=img_path,
    )

    assert isinstance(result, ForensicAnalysisResult)
    assert result.overall_forensic_score >= 0.85
    assert result.forensics_risk_score <= 15.0
    assert len(result.detected_clones) == 0
    assert result.heatmap_image_path is not None
    assert Path(result.heatmap_image_path).exists()


def test_forensic_service_spec02_contract(tmp_path: Path):
    """Verify analyze_to_pipeline_output returns valid SPEC-02 ForensicsOutput contract."""
    service = get_forensic_service()

    img = np.full((400, 400, 3), 240, dtype=np.uint8)

    output = service.analyze_to_pipeline_output(
        document_id="spec02_forensic_doc",
        raw_image_or_path=img,
    )

    assert isinstance(output, ForensicsOutput)
    assert output.document_id == "spec02_forensic_doc"
    assert 0.0 <= output.ela_score <= 1.0
    assert 0.0 <= output.forensics_risk_score <= 100.0
    assert isinstance(output.copy_move_detected, bool)


def test_forensic_execution_time_under_five_seconds(tmp_path: Path):
    """NFR-03: Performance requirement (< 5.0s execution time)."""
    service = get_forensic_service()

    # 1000x1000 realistic image
    img = np.full((1000, 1000, 3), 245, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for i in range(10):
        cv2.putText(
            img, f"Certificate line text number {i}", (100, 100 + i * 80), font, 0.7, (0, 0, 0), 1
        )

    start = time.perf_counter()
    result = service.analyze(
        document_id="perf_forensic_doc",
        raw_image_or_path=img,
    )
    elapsed = time.perf_counter() - start

    assert elapsed < 5.0
    assert result.execution_time_ms < 5000.0
