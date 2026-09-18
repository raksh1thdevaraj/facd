import hashlib
import time
import uuid
from pathlib import Path

import cv2
import numpy as np

from app.modules.preprocessing.artifact_manager import PreprocessingArtifactManager
from app.modules.preprocessing.diagnostics import run_preprocessing_diagnostics
from app.modules.preprocessing.service import PreprocessingService


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_end_to_end_preprocessing_under_5s(tmp_path: Path):
    # 1. Create a large, realistic synthetic certificate image (2400x1800)
    cert_img = np.ones((1800, 2400, 3), dtype=np.uint8) * 248
    for y in range(300, 1600, 120):
        cv2.putText(
            cert_img,
            "DEPARTMENT OF ACADEMIC AFFAIRS - OFFICIAL TRANSCRIPT",
            (250, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (15, 15, 15),
            2,
            cv2.LINE_AA,
        )

    raw_path = tmp_path / "original_certificate.png"
    cv2.imwrite(str(raw_path), cert_img)

    # 2. Record SHA-256 before preprocessing
    sha_before = compute_sha256(raw_path)

    artifact_manager = PreprocessingArtifactManager(target_dir=tmp_path / "preprocessed")
    service = PreprocessingService(artifact_manager=artifact_manager)

    cert_id = uuid.uuid4()

    t0 = time.perf_counter()
    result = service.preprocess(cert_id, raw_path)
    elapsed_sec = time.perf_counter() - t0

    # Verification: Performance < 5.0 seconds (NFR-03)
    assert elapsed_sec < 5.0

    # Verification: Original raw file is strictly untouched and immutable (TC-PRE-05)
    sha_after = compute_sha256(raw_path)
    assert sha_before == sha_after

    # Verification: Output artifact persistence
    assert result.enhanced_image_path is not None
    assert result.enhanced_image_path.exists()
    assert result.binarized_image_path is not None
    assert result.binarized_image_path.exists()
    assert result.thumbnail_path is not None
    assert result.thumbnail_path.exists()

    # Verification: Conformance with SPEC-02 data contract
    pipeline_out = result.to_pipeline_output(document_id=str(cert_id))
    assert pipeline_out.document_id == str(cert_id)
    assert pipeline_out.processed_image_path == str(result.enhanced_image_path.resolve())
    assert pipeline_out.thumbnail_path == str(result.thumbnail_path.resolve())
    assert pipeline_out.original_width == 2400
    assert pipeline_out.original_height == 1800
    assert pipeline_out.processed_width >= 1200
    assert pipeline_out.contrast_applied is True
    assert pipeline_out.noise_reduction_applied is True


def test_preprocessing_diagnostics():
    diag = run_preprocessing_diagnostics()
    assert diag["status"] == "ok"
    assert "benchmark_duration_ms" in diag
    assert diag["benchmark_duration_ms"] < diag["target_max_ms"]
