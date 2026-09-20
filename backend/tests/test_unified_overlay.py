"""Unit tests for UnifiedOverlayRenderer."""

from pathlib import Path

import numpy as np
from PIL import Image

from app.modules.explainability.unified_overlay import UnifiedOverlayRenderer
from app.schemas.explainability import (
    FindingSeverity,
    NormalizedBox,
    UnifiedAnomalyBox,
)
from app.schemas.primitives import PixelBoundingBox


def test_unified_overlay_rendering(tmp_path: Path):
    """Verify multi-layer visual evidence overlay generates valid image with legend
    (TC-EXP-02, TC-EXP-05).
    """
    raw_img_path = tmp_path / "cert_raw.png"
    Image.new("RGB", (800, 1000), color=(245, 245, 240)).save(raw_img_path)

    # Anomaly box
    box1 = UnifiedAnomalyBox(
        id="box_1",
        category="TEXT",
        severity=FindingSeverity.MAJOR,
        box=PixelBoundingBox(x=100, y=200, width=300, height=40),
        normalized_box=NormalizedBox(x=0.125, y=0.2, w=0.375, h=0.04),
        label="Text: Baseline Drift",
        description="Text baseline sits 4px below expected line",
        color="#D50000",
    )

    renderer = UnifiedOverlayRenderer()
    out_path = tmp_path / "unified_overlay.png"

    # Also test with mock heatmap array
    dummy_heatmap = np.zeros((1000, 800), dtype=np.float32)
    dummy_heatmap[150:250, 100:400] = 0.8  # hotspot

    res = renderer.render(
        raw_image_path=raw_img_path,
        output_path=out_path,
        anomalies=[box1],
        heatmap_array=dummy_heatmap,
    )

    assert res.exists()
    assert res.stat().st_size > 0

    # Verify generated image has correct dimensions
    with Image.open(res) as img:
        assert img.size == (800, 1000)
