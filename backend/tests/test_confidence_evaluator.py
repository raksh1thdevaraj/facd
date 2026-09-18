import pytest

from app.modules.ocr.confidence_evaluator import ConfidenceEvaluator
from app.modules.ocr.field_extractors.base_extractor import ExtractedField
from app.modules.ocr.token_builder import TokenBuilder
from app.schemas.primitives import BoundingBox, PixelBoundingBox


def test_confidence_evaluation_and_flagging():
    evaluator = ConfidenceEvaluator(threshold=0.70)

    # Token 1: High confidence (0.95)
    tok1 = TokenBuilder.create_token("ALICE", 0.95, 100, 100, 50, 20, 1000, 1000)
    # Token 2: Low confidence (0.55)
    tok2 = TokenBuilder.create_token("1MS20CS001", 0.55, 100, 200, 120, 20, 1000, 1000)

    dummy_norm = BoundingBox(x1=0.1, y1=0.1, x2=0.3, y2=0.2)
    dummy_pix = PixelBoundingBox(x=100, y=100, width=200, height=50)

    field_high = ExtractedField(
        field_name="student_name",
        value="ALICE",
        raw_text="ALICE",
        confidence=0.95,
        bounding_box=dummy_norm,
        pixel_bounding_box=dummy_pix,
        source_tokens=[tok1],
    )

    field_low = ExtractedField(
        field_name="register_number",
        value="1MS20CS001",
        raw_text="1MS20CS001",
        confidence=0.55,
        bounding_box=dummy_norm,
        pixel_bounding_box=dummy_pix,
        source_tokens=[tok2],
    )

    extracted = {
        "student_name": field_high,
        "register_number": field_low,
    }

    cert_fields, field_dtos, low_flag, avg_conf = evaluator.evaluate_and_map_fields(
        extracted, [tok1, tok2]
    )

    # TC-OCR-04: Confidence score calculation and < 0.70 flagging
    assert low_flag is True
    assert field_dtos["student_name"].is_flagged is False
    assert field_dtos["student_name"].confidence == 0.95
    assert field_dtos["register_number"].is_flagged is True
    assert field_dtos["register_number"].confidence == 0.55

    # Check CertificateFields mapping
    assert cert_fields.student_name == "ALICE"
    assert cert_fields.student_name_confidence == 0.95
    assert cert_fields.register_number == "1MS20CS001"
    assert cert_fields.register_number_confidence == 0.55

    # Average confidence: (0.95 + 0.55) / 2 = 0.75
    assert avg_conf == pytest.approx(0.75, rel=1e-2)
