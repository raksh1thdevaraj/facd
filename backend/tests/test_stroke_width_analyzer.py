import cv2
import numpy as np

from app.modules.ocr.spatial_analyzer import TextLine
from app.modules.ocr.token_builder import TokenBuilder
from app.modules.text_consistency.stroke_width_analyzer import StrokeWidthAnalyzer
from app.schemas.text_consistency import AnomalyType


def test_uniform_stroke_weights_produce_clean_score():
    """Verify uniform stroke weights across text line yield stroke consistency score >= 0.90."""
    analyzer = StrokeWidthAnalyzer()

    # Create white canvas 300x800
    img = np.full((300, 800, 3), 255, dtype=np.uint8)

    # Render regular text with thickness=1
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "Bachelor", (50, 150), font, 1.0, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "of", (210, 150), font, 1.0, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "Science", (260, 150), font, 1.0, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "Degree", (410, 150), font, 1.0, (0, 0, 0), 1, cv2.LINE_AA)

    tokens = [
        TokenBuilder.create_token("Bachelor", 0.95, 45, 120, 150, 40, 800, 300),
        TokenBuilder.create_token("of", 0.95, 205, 120, 45, 40, 800, 300),
        TokenBuilder.create_token("Science", 0.95, 255, 120, 140, 40, 800, 300),
        TokenBuilder.create_token("Degree", 0.95, 405, 120, 130, 40, 800, 300),
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze(img, [line])
    assert score >= 0.90
    assert len(anomalies) == 0


def test_detects_bold_word_stroke_discrepancy():
    """Detect stroke weight discrepancy when one word is artificially bolded."""
    analyzer = StrokeWidthAnalyzer()

    img = np.full((300, 900, 3), 255, dtype=np.uint8)
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Words 1, 2, 4 rendered with thickness=1
    cv2.putText(img, "Grade", (50, 150), font, 1.0, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(img, "is", (170, 150), font, 1.0, (0, 0, 0), 1, cv2.LINE_AA)
    # Word 3 rendered with bold thickness=4
    cv2.putText(img, "DISTINCTION", (220, 150), font, 1.0, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(img, "Awarded", (470, 150), font, 1.0, (0, 0, 0), 1, cv2.LINE_AA)

    tokens = [
        TokenBuilder.create_token("Grade", 0.95, 45, 115, 110, 45, 900, 300),
        TokenBuilder.create_token("is", 0.95, 165, 115, 45, 45, 900, 300),
        TokenBuilder.create_token("DISTINCTION", 0.95, 215, 115, 240, 45, 900, 300),
        TokenBuilder.create_token("Awarded", 0.95, 465, 115, 140, 45, 900, 300),
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze(img, [line])
    assert score < 0.85
    assert len(anomalies) >= 1

    stroke_anomaly = next(
        a for a in anomalies if a.anomaly_type == AnomalyType.STROKE_WEIGHT_DISCREPANCY
    )
    assert stroke_anomaly.token_text == "DISTINCTION"
    assert "heavier/bolder" in stroke_anomaly.description


def test_stroke_analyzer_handles_blank_or_missing_image():
    """Missing or empty image is handled gracefully without exception."""
    analyzer = StrokeWidthAnalyzer()
    tokens = [TokenBuilder.create_token("Test", 0.95, 10, 10, 50, 20, 100, 100)]
    line = TextLine.from_tokens(tokens)

    score_none, anomalies_none = analyzer.analyze(None, [line])
    assert score_none == 1.0
    assert len(anomalies_none) == 0

    empty_img = np.zeros((0, 0), dtype=np.uint8)
    score_empty, anomalies_empty = analyzer.analyze(empty_img, [line])
    assert score_empty == 1.0
    assert len(anomalies_empty) == 0
