"""Unit tests for CoordinateMapper (spatial scaling and clamping)."""

import numpy as np

from app.modules.explainability.coordinate_mapper import CoordinateMapper
from app.schemas.primitives import PixelBoundingBox


def test_coordinate_scaling():
    """Verify box scaling from 512x512 to 1024x1024 raw canvas (TC-EXP-03)."""
    mapper = CoordinateMapper(orig_width=1024, orig_height=1024, proc_width=512, proc_height=512)
    # (x=100, y=50, w=40, h=20) -> should scale by 2.0
    pbox = mapper.map_box(100, 50, 40, 20)

    assert isinstance(pbox, PixelBoundingBox)
    assert pbox.x == 200
    assert pbox.y == 100
    assert pbox.width == 80
    assert pbox.height == 40


def test_coordinate_boundary_clamping():
    """Verify boundary clamping prevents coordinates exceeding canvas bounds."""
    mapper = CoordinateMapper(orig_width=1000, orig_height=1000, proc_width=500, proc_height=500)
    # Out of bounds coordinates (x=490, w=50) -> scaled x=980, w=100 would exceed 1000
    pbox = mapper.map_box(490, 490, 50, 50)

    assert pbox.x + pbox.width <= 1000
    assert pbox.y + pbox.height <= 1000


def test_normalized_mapping():
    """Verify normalized [0, 1] coordinates map to absolute pixels and back."""
    mapper = CoordinateMapper(orig_width=800, orig_height=600)
    pbox, nbox = mapper.map_normalized(0.1, 0.2, 0.5, 0.3)

    assert pbox.x == 80
    assert pbox.y == 120
    assert pbox.width == 400
    assert pbox.height == 180
    assert nbox.x == 0.1
    assert nbox.y == 0.2


def test_map_points():
    """Verify scaling array of keypoints."""
    mapper = CoordinateMapper(orig_width=1000, orig_height=800, proc_width=500, proc_height=400)
    pts = np.array([[10, 20], [50, 60]], dtype=np.float32)
    scaled_pts = mapper.map_points(pts)

    assert scaled_pts.shape == (2, 2)
    assert scaled_pts[0, 0] == 20
    assert scaled_pts[0, 1] == 40
