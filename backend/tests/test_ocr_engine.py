import numpy as np
import pytest

from app.modules.ocr.engine_factory import EngineFactory
from app.modules.ocr.mock_engine import MockOCREngine
from app.modules.ocr.spatial_analyzer import SpatialLayoutAnalyzer
from app.modules.ocr.token_builder import GeometricBoundingBox, Point, TokenBuilder


def test_geometric_bounding_box_and_normalization():
    polygon = [[100, 200], [300, 200], [300, 250], [100, 250]]
    box = GeometricBoundingBox.from_polygon(polygon)

    assert box.x_min == 100
    assert box.x_max == 300
    assert box.y_min == 200
    assert box.y_max == 250
    assert box.width == 200
    assert box.height == 50
    assert box.center == Point(200.0, 225.0)

    # Test normalization into [0.0, 1.0]
    norm_bbox, pix_bbox = box.to_relative_bbox(img_width=1000, img_height=500)
    assert norm_bbox.x_min == pytest.approx(0.1, rel=1e-3)
    assert norm_bbox.x_max == pytest.approx(0.3, rel=1e-3)
    assert norm_bbox.y_min == pytest.approx(0.4, rel=1e-3)
    assert norm_bbox.y_max == pytest.approx(0.5, rel=1e-3)

    assert pix_bbox.x == 100
    assert pix_bbox.y == 200
    assert pix_bbox.width == 200
    assert pix_bbox.height == 50


def test_spatial_line_grouping_and_reading_order():
    img_w, img_h = 1000, 800

    # Create tokens simulating two distinct lines in arbitrary order
    # Line 2 (y=400): "JOHN DOE"
    tok_john = TokenBuilder.create_token("JOHN", 0.95, 100, 400, 80, 25, img_w, img_h)
    tok_doe = TokenBuilder.create_token("DOE", 0.96, 190, 402, 60, 25, img_w, img_h)

    # Line 1 (y=200): "VISVESVARAYA TECHNOLOGICAL UNIVERSITY"
    tok_vtu1 = TokenBuilder.create_token("VISVESVARAYA", 0.99, 100, 200, 150, 30, img_w, img_h)
    tok_vtu2 = TokenBuilder.create_token("TECHNOLOGICAL", 0.98, 260, 201, 140, 30, img_w, img_h)
    tok_vtu3 = TokenBuilder.create_token("UNIVERSITY", 0.97, 410, 199, 120, 30, img_w, img_h)

    # Shuffle tokens
    unordered_tokens = [tok_doe, tok_vtu3, tok_john, tok_vtu1, tok_vtu2]

    lines = SpatialLayoutAnalyzer.group_tokens_into_lines(unordered_tokens)

    # Should produce exactly 2 lines, ordered from top to bottom
    assert len(lines) == 2

    # Top line should be the university
    assert lines[0].text == "VISVESVARAYA TECHNOLOGICAL UNIVERSITY"
    assert lines[0].pixel_bbox.y < 250
    assert len(lines[0].tokens) == 3

    # Bottom line should be the student
    assert lines[1].text == "JOHN DOE"
    assert lines[1].pixel_bbox.y > 350
    assert len(lines[1].tokens) == 2


def test_engine_factory_and_mock_engine():
    engines = EngineFactory.get_available_engines()
    assert "mock" in engines
    assert engines["mock"] is True

    mock_engine = EngineFactory.get_engine("mock")
    assert isinstance(mock_engine, MockOCREngine)
    assert mock_engine.engine_name == "mock"

    canvas = np.ones((800, 1000, 3), dtype=np.uint8) * 255
    tokens = mock_engine.extract_tokens(canvas)

    assert len(tokens) > 5
    assert all(0.0 <= t.confidence <= 1.0 for t in tokens)
    assert any("VISVESVARAYA" in t.text for t in tokens)
    assert any("1MS20CS001" in t.text for t in tokens)


def test_token_builder_from_easyocr_and_tesseract():
    # Test from_easyocr_result
    raw_easyocr = [
        ([[50, 100], [200, 100], [200, 130], [50, 130]], "BACHELOR OF TECHNOLOGY", 0.94),
        ([[50, 200], [150, 200], [150, 230], [50, 230]], "GRADE: 9.2", 0.91),
    ]
    tokens = TokenBuilder.from_easyocr_result(raw_easyocr, img_width=1000, img_height=1000)
    assert len(tokens) == 2
    assert tokens[0].text == "BACHELOR OF TECHNOLOGY"
    assert tokens[0].confidence == pytest.approx(0.94, rel=1e-2)
    assert tokens[0].pixel_bbox.x == 50
    assert tokens[0].pixel_bbox.width == 150

    # Test from_tesseract_data
    raw_tess = {
        "text": ["", "UNIVERSITY", "OF", "OXFORD"],
        "conf": ["-1", "95", "96", "98"],
        "left": [0, 100, 220, 260],
        "top": [0, 50, 50, 50],
        "width": [0, 110, 35, 80],
        "height": [0, 25, 25, 25],
    }
    tess_tokens = TokenBuilder.from_tesseract_data(raw_tess, img_width=1000, img_height=1000)
    assert len(tess_tokens) == 3
    assert [t.text for t in tess_tokens] == ["UNIVERSITY", "OF", "OXFORD"]
    assert all(t.confidence >= 0.95 for t in tess_tokens)


def test_spatial_analyzer_proximity_and_band_queries():
    img_w, img_h = 1000, 1000
    t1 = TokenBuilder.create_token("NAME:", 0.95, 100, 200, 60, 25, img_w, img_h)
    t2 = TokenBuilder.create_token("ALICE", 0.95, 170, 200, 70, 25, img_w, img_h)
    t3 = TokenBuilder.create_token("FAR_AWAY", 0.95, 800, 200, 100, 25, img_w, img_h)

    line = SpatialLayoutAnalyzer.group_tokens_into_lines([t1, t2, t3])[0]
    right_tokens = SpatialLayoutAnalyzer.find_tokens_to_right(t1, line, max_gap_px=50)

    assert len(right_tokens) == 1
    assert right_tokens[0].text == "ALICE"

    # Band filter test
    lines = [line]
    band_lines = SpatialLayoutAnalyzer.filter_by_vertical_band(lines, min_rel_y=0.1, max_rel_y=0.3)
    assert len(band_lines) == 1

    empty_band = SpatialLayoutAnalyzer.filter_by_vertical_band(lines, min_rel_y=0.5, max_rel_y=0.9)
    assert len(empty_band) == 0
