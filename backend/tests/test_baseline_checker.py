from app.modules.ocr.spatial_analyzer import TextLine
from app.modules.ocr.token_builder import TokenBuilder
from app.modules.text_consistency.baseline_checker import BaselineAlignmentAnalyzer
from app.schemas.text_consistency import AnomalyType


def test_aligned_baseline_produces_high_score():
    """Verify that perfectly aligned text line yields baseline score >= 0.95."""
    analyzer = BaselineAlignmentAnalyzer()

    # 5 words on baseline y_bottom = 120
    tokens = [
        TokenBuilder.create_token("Bachelor", 0.98, 100, 100, 70, 20, 1000, 1000),
        TokenBuilder.create_token("of", 0.98, 180, 100, 20, 20, 1000, 1000),
        TokenBuilder.create_token("Science", 0.98, 210, 100, 60, 20, 1000, 1000),
        TokenBuilder.create_token("in", 0.98, 280, 100, 20, 20, 1000, 1000),
        TokenBuilder.create_token("Computer", 0.98, 310, 100, 80, 20, 1000, 1000),
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score >= 0.95
    assert len(anomalies) == 0


def test_detects_raised_word_on_baseline():
    """TC-TXT-02: Detect baseline drift when a spliced word is raised by 6px."""
    analyzer = BaselineAlignmentAnalyzer()

    # 5 words: 1st, 2nd, 4th, 5th at y=100 (bottom=120).
    # 3rd token is raised by 6px: y=94 (bottom=114).
    tokens = [
        TokenBuilder.create_token("First", 0.95, 100, 100, 50, 20, 1000, 1000),
        TokenBuilder.create_token("Class", 0.95, 160, 100, 50, 20, 1000, 1000),
        TokenBuilder.create_token("with", 0.95, 220, 94, 45, 20, 1000, 1000),  # Raised by 6px
        TokenBuilder.create_token("High", 0.95, 275, 100, 45, 20, 1000, 1000),
        TokenBuilder.create_token("Honors", 0.95, 330, 100, 65, 20, 1000, 1000),
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score < 0.85
    assert len(anomalies) >= 1

    drift_anomaly = next(a for a in anomalies if a.anomaly_type == AnomalyType.BASELINE_DRIFT)
    assert drift_anomaly.token_text == "with"
    assert drift_anomaly.severity >= 0.50
    assert "deviates" in drift_anomaly.description


def test_descender_filtering_avoids_false_positives():
    """Verify words with natural descenders ('g', 'p', 'y') do not trigger false anomalies."""
    analyzer = BaselineAlignmentAnalyzer()

    # Words like "Technology" contain 'g', 'y'. The bottom is physically lower by ~4px.
    tokens = [
        TokenBuilder.create_token("Department", 0.95, 100, 100, 90, 20, 1000, 1000),
        TokenBuilder.create_token("of", 0.95, 200, 100, 20, 20, 1000, 1000),
        TokenBuilder.create_token("Computer", 0.95, 230, 100, 80, 20, 1000, 1000),
        TokenBuilder.create_token(
            "Technology", 0.95, 320, 100, 95, 24, 1000, 1000
        ),  # Descender 'g', 'y'
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score >= 0.90
    assert len(anomalies) == 0


def test_empty_or_short_lines_handled_gracefully():
    """Lines with fewer than 3 tokens should not crash and yield neutral score."""
    analyzer = BaselineAlignmentAnalyzer()
    tokens = [TokenBuilder.create_token("Name", 0.95, 100, 100, 40, 20, 1000, 1000)]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score == 1.0
    assert len(anomalies) == 0

    score_empty, anomalies_empty = analyzer.analyze([])
    assert score_empty == 1.0
    assert len(anomalies_empty) == 0
