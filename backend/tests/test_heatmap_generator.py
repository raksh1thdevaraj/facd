from pathlib import Path

import cv2
import numpy as np

from app.modules.forensics.heatmap_generator import ForensicHeatmapGenerator
from app.schemas.forensics import CloneMatch
from app.schemas.primitives import BoundingBox, PixelBoundingBox


def test_heatmap_file_generation(tmp_path: Path):
    """TC-FOR-05: Verify high-contrast thermal heatmap is properly generated and saved."""
    raw_img = np.full((500, 700, 3), 240, dtype=np.uint8)
    ela_map = np.zeros((500, 700, 3), dtype=np.uint8)
    # Add an ELA hotspot
    ela_map[100:200, 100:200] = 200

    noise_map = np.zeros((500, 700), dtype=np.uint8)
    noise_map[300:400, 300:400] = 220

    out_file = tmp_path / "forensics_heatmap.png"

    saved_path = ForensicHeatmapGenerator.generate_composite_heatmap(
        raw_image=raw_img,
        ela_map=ela_map,
        clone_matches=[],
        noise_map=noise_map,
        output_path=out_file,
    )

    assert saved_path.exists()
    assert str(saved_path) == str(out_file)

    rendered = cv2.imread(str(saved_path))
    assert rendered is not None
    assert rendered.shape == (500, 700, 3)


def test_heatmap_renders_clone_connection_lines(tmp_path: Path):
    """Verify clone matches draw bounding boxes and connecting lines on the heatmap."""
    raw_img = np.full((600, 800, 3), 250, dtype=np.uint8)

    clone = CloneMatch(
        source_bbox=BoundingBox(x1=0.1, y1=0.1, x2=0.2, y2=0.2),
        target_bbox=BoundingBox(x1=0.5, y1=0.5, x2=0.6, y2=0.6),
        source_pixel_bbox=PixelBoundingBox(x=80, y=80, width=80, height=80),
        target_pixel_bbox=PixelBoundingBox(x=400, y=400, width=80, height=80),
        inlier_count=12,
        confidence=0.92,
        displacement_vector=(320.0, 320.0),
    )

    out_file = tmp_path / "clone_heatmap.png"

    saved_path = ForensicHeatmapGenerator.generate_composite_heatmap(
        raw_image=raw_img,
        ela_map=None,
        clone_matches=[clone],
        noise_map=None,
        output_path=out_file,
    )

    assert saved_path.exists()
    rendered = cv2.imread(str(saved_path))
    assert rendered is not None
    assert rendered.shape == (600, 800, 3)
