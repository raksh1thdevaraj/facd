from app.modules.ocr.token_builder import TokenBuilder
from app.modules.text_consistency.format_checker import FormatChecker
from app.schemas.text_consistency import AnomalyType


def test_clean_text_passes_cleanly():
    """Verify that normally formatted words yield format consistency score 1.0."""
    checker = FormatChecker()
    tokens = [
        TokenBuilder.create_token("UNIVERSITY", 0.95, 100, 100, 120, 25, 1000, 1000),
        TokenBuilder.create_token("OF", 0.95, 230, 100, 30, 25, 1000, 1000),
        TokenBuilder.create_token("CAMBRIDGE", 0.95, 270, 100, 130, 25, 1000, 1000),
        TokenBuilder.create_token("First", 0.95, 100, 150, 50, 20, 1000, 1000),
        TokenBuilder.create_token("Class", 0.95, 160, 150, 50, 20, 1000, 1000),
    ]

    score, anomalies = checker.analyze(tokens)
    assert score == 1.0
    assert len(anomalies) == 0


def test_detects_cyrillic_homoglyph():
    """Detect homoglyph evasion when a Cyrillic character is embedded inside Latin text."""
    checker = FormatChecker()

    # In "Pаssed", the 'а' is Cyrillic small letter a (U+0430)
    cyrillic_a = "\u0430"
    forged_word = f"P{cyrillic_a}ssed"

    tokens = [
        TokenBuilder.create_token("Successfully", 0.95, 100, 100, 110, 20, 1000, 1000),
        TokenBuilder.create_token(forged_word, 0.95, 220, 100, 70, 20, 1000, 1000),
        TokenBuilder.create_token("Examination", 0.95, 300, 100, 120, 20, 1000, 1000),
    ]

    score, anomalies = checker.analyze(tokens)
    assert score < 1.0
    assert len(anomalies) >= 1

    homoglyph_anomaly = next(
        a for a in anomalies if a.anomaly_type == AnomalyType.FORMAT_IRREGULARITY
    )
    assert "Homoglyph" in homoglyph_anomaly.description
    assert homoglyph_anomaly.severity >= 0.90


def test_detects_erratic_capitalization():
    """Detect erratic casing anomaly inside a word like 'cOMPUTER'."""
    checker = FormatChecker()

    tokens = [
        TokenBuilder.create_token("Bachelor", 0.95, 100, 100, 70, 20, 1000, 1000),
        TokenBuilder.create_token("of", 0.95, 180, 100, 20, 20, 1000, 1000),
        TokenBuilder.create_token("cOMPUTER", 0.95, 210, 100, 90, 20, 1000, 1000),  # Erratic casing
        TokenBuilder.create_token("Science", 0.95, 310, 100, 70, 20, 1000, 1000),
    ]

    score, anomalies = checker.analyze(tokens)
    assert score < 1.0
    assert len(anomalies) >= 1

    caps_anomaly = next(a for a in anomalies if a.anomaly_type == AnomalyType.FORMAT_IRREGULARITY)
    assert "capitalization" in caps_anomaly.description
    assert caps_anomaly.token_text == "cOMPUTER"
