from pathlib import Path

import cv2
import numpy as np

from app.modules.ocr.mock_engine import MockOCREngine
from app.modules.ocr.service import OCRService
from app.schemas.ocr import OCRConfig
from app.schemas.pipeline import OCROutput


def test_ocr_service_end_to_end_and_spec02_compliance(tmp_path: Path):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()

    # Create synthetic certificate image
    img = np.ones((1200, 1600, 3), dtype=np.uint8) * 255
    cv2.putText(
        img, "ACADEMIC CERTIFICATE", (500, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2
    )
    img_path = tmp_path / "cert_test.png"
    cv2.imwrite(str(img_path), img)

    mock_engine = MockOCREngine()
    config = OCRConfig(engine="mock", generate_overlay=True, confidence_threshold=0.70)
    service = OCRService(engine=mock_engine, config=config, report_dir=report_dir)

    doc_id = "doc-test-12345"
    result = service.process_document(doc_id, img_path)

    # 1. Verify result DTO
    assert result.document_id == doc_id
    assert result.engine_used == "mock"
    assert result.token_count > 10
    assert result.average_ocr_confidence >= 0.90
    assert result.low_confidence_flag is False
    assert result.execution_time_ms < 5000.0  # NFR-03 benchmark < 10s

    # 2. Verify academic fields were extracted
    fields = result.fields
    assert fields.student_name == "RAKSHITH DEVARAJA"
    assert fields.register_number == "1MS20CS001"
    assert "Bachelor of Technology" in (fields.course_degree or "")
    assert "VISVESVARAYA" in (fields.institution_name or "")
    assert fields.issue_date == "2024-06-15"
    assert "9.45" in (fields.grade_or_marks or "")
    assert fields.certificate_number == "VTU-2024-889921"

    # 3. Verify overlay file was saved on disk
    assert result.overlay_path is not None
    overlay_path = Path(result.overlay_path)
    assert overlay_path.exists()
    assert overlay_path.stat().st_size > 0

    # 4. Verify SPEC-02 OCROutput contract conversion
    pipeline_output = service.extract_to_pipeline_output(doc_id, img_path)
    assert isinstance(pipeline_output, OCROutput)
    assert pipeline_output.document_id == doc_id
    assert pipeline_output.fields.student_name == "RAKSHITH DEVARAJA"
    assert pipeline_output.fields.register_number == "1MS20CS001"
    assert len(pipeline_output.tokens) > 0
    assert all(0.0 <= t.confidence <= 1.0 for t in pipeline_output.tokens)
