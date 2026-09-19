from app.modules.ocr.spatial_analyzer import TextLine
from app.modules.ocr.token_builder import TokenBuilder
from app.modules.text_consistency.spacing_analyzer import CharacterSpacingAnalyzer
from app.schemas.text_consistency import AnomalyType


def test_uniform_spacing_produces_clean_score():
    """Verify that regular inter-token spacing yields high consistency score >= 0.95."""
    analyzer = CharacterSpacingAnalyzer()

    # Even gaps of 10px between tokens
    tokens = [
        TokenBuilder.create_token("Roll", 0.95, 100, 100, 40, 20, 1000, 1000),  # Ends 140
        TokenBuilder.create_token(
            "Number", 0.95, 150, 100, 60, 20, 1000, 1000
        ),  # Gap: 10, ends 210
        TokenBuilder.create_token("is", 0.95, 220, 100, 20, 20, 1000, 1000),  # Gap: 10, ends 240
        TokenBuilder.create_token("2021001", 0.95, 250, 100, 70, 20, 1000, 1000),  # Gap: 10
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score >= 0.95
    assert len(anomalies) == 0


def test_detects_overlapping_tokens():
    """TC-TXT-03: Detect token collision when a spliced word overlaps previous text (gap < 0)."""
    analyzer = CharacterSpacingAnalyzer()

    # Token 2 starts at x=195 while Token 1 ends at x=200 (overlap of 5px)
    tokens = [
        TokenBuilder.create_token("Candidate", 0.95, 100, 100, 100, 20, 1000, 1000),  # Ends 200
        TokenBuilder.create_token(
            "Name", 0.95, 195, 100, 50, 20, 1000, 1000
        ),  # Starts 195: OVERLAP -5px
        TokenBuilder.create_token("John", 0.95, 260, 100, 40, 20, 1000, 1000),  # Gap: 15
        TokenBuilder.create_token("Doe", 0.95, 315, 100, 40, 20, 1000, 1000),  # Gap: 15
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score < 0.85
    assert len(anomalies) >= 1

    overlap_anomaly = next(
        a for a in anomalies if a.anomaly_type == AnomalyType.SPACING_IRREGULARITY
    )
    assert "Collision/overlap" in overlap_anomaly.description
    assert "Candidate" in overlap_anomaly.token_text
    assert overlap_anomaly.severity >= 0.60


def test_detects_compressed_spacing():
    """Detect artificially compressed spacing when words are squeezed into a narrow box."""
    analyzer = CharacterSpacingAnalyzer()

    # Median gap is 15px. Gap between token 2 and 3 is 1px (< 0.20 * 15px)
    tokens = [
        TokenBuilder.create_token("Registration", 0.95, 100, 100, 100, 20, 1000, 1000),  # Ends 200
        TokenBuilder.create_token("No", 0.95, 215, 100, 30, 20, 1000, 1000),  # Gap: 15, ends 245
        TokenBuilder.create_token(
            "1MS20CS001", 0.95, 246, 100, 110, 20, 1000, 1000
        ),  # Gap: 1px (micro)
        TokenBuilder.create_token("Valid", 0.95, 371, 100, 50, 20, 1000, 1000),  # Gap: 15px
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score < 0.85
    assert len(anomalies) >= 1

    comp_anomaly = next(a for a in anomalies if a.anomaly_type == AnomalyType.SPACING_IRREGULARITY)
    assert "Compressed" in comp_anomaly.description


def test_detects_stretched_spacing():
    """Detect stretched inter-token spacing indicative of deleted/replaced text."""
    analyzer = CharacterSpacingAnalyzer()

    # Median gap is 10px. Gap between token 2 and 3 is 45px (> 2.5 * 10px)
    tokens = [
        TokenBuilder.create_token("Grade", 0.95, 100, 100, 50, 20, 1000, 1000),  # Ends 150
        TokenBuilder.create_token("Point", 0.95, 160, 100, 45, 20, 1000, 1000),  # Gap: 10, ends 205
        TokenBuilder.create_token(
            "Average", 0.95, 250, 100, 65, 20, 1000, 1000
        ),  # Gap: 45px (macro)
        TokenBuilder.create_token("8.9", 0.95, 325, 100, 30, 20, 1000, 1000),  # Gap: 10px
    ]
    line = TextLine.from_tokens(tokens)

    score, anomalies = analyzer.analyze([line])
    assert score < 0.85
    assert len(anomalies) >= 1

    macro_anomaly = next(a for a in anomalies if a.anomaly_type == AnomalyType.SPACING_IRREGULARITY)
    assert "Stretched" in macro_anomaly.description
