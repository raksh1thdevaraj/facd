from app.modules.ocr.spatial_analyzer import TextLine
from app.modules.ocr.token_builder import TokenBuilder
from app.modules.text_consistency.font_size_analyzer import FontSizeAnalyzer
from app.schemas.text_consistency import AnomalyType


def test_consistent_font_sizes_produce_clean_score():
    """Verify that lines with uniform token heights receive font size score >= 0.95."""
    analyzer = FontSizeAnalyzer()

    tokens = [
        TokenBuilder.create_token("Master", 0.95, 100, 100, 60, 20, 1000, 1000),
        TokenBuilder.create_token("of", 0.95, 170, 100, 20, 19, 1000, 1000),
        TokenBuilder.create_token("Business", 0.95, 200, 100, 80, 21, 1000, 1000),
        TokenBuilder.create_token("Administration", 0.95, 290, 100, 120, 20, 1000, 1000),
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score >= 0.95
    assert len(anomalies) == 0


def test_detects_oversized_font():
    """TC-TXT-01: Detect oversized font when a spliced token is 18px high within a 12px line."""
    analyzer = FontSizeAnalyzer()

    # Surrounding tokens have 12px height; "DISTINCTION" has 18px height (50% increase)
    tokens = [
        TokenBuilder.create_token("awarded", 0.95, 100, 100, 60, 12, 1000, 1000),
        TokenBuilder.create_token("with", 0.95, 170, 100, 40, 12, 1000, 1000),
        TokenBuilder.create_token(
            "DISTINCTION", 0.95, 220, 94, 110, 18, 1000, 1000
        ),  # 18px vs 12px
        TokenBuilder.create_token("grade", 0.95, 340, 100, 50, 12, 1000, 1000),
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score < 0.85
    assert len(anomalies) >= 1

    size_anomaly = next(a for a in anomalies if a.anomaly_type == AnomalyType.FONT_SIZE_MISMATCH)
    assert size_anomaly.token_text == "DISTINCTION"
    assert "oversized" in size_anomaly.description
    assert size_anomaly.severity >= 0.50


def test_detects_undersized_font():
    """Detect undersized font when a spliced token is 13px high within a 20px line."""
    analyzer = FontSizeAnalyzer()

    tokens = [
        TokenBuilder.create_token("Degree", 0.95, 100, 100, 60, 20, 1000, 1000),
        TokenBuilder.create_token("of", 0.95, 170, 100, 25, 20, 1000, 1000),
        TokenBuilder.create_token("Doctor", 0.95, 205, 100, 60, 13, 1000, 1000),  # 13px vs 20px
        TokenBuilder.create_token("Philosophy", 0.95, 275, 100, 90, 20, 1000, 1000),
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score < 0.85
    assert len(anomalies) >= 1

    size_anomaly = next(a for a in anomalies if a.anomaly_type == AnomalyType.FONT_SIZE_MISMATCH)
    assert size_anomaly.token_text == "Doctor"
    assert "undersized" in size_anomaly.description


def test_empty_lines_handled_gracefully():
    """Empty line list returns score 1.0 and no anomalies."""
    analyzer = FontSizeAnalyzer()
    score, anomalies = analyzer.analyze([])
    assert score == 1.0
    assert len(anomalies) == 0
