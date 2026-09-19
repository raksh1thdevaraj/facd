import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from app.modules.forensics.ela_analyzer import ELAAnalyzer


def test_pristine_image_high_ela_score(tmp_path: Path):
    """Verify that a uniformly compressed JPEG image produces high ELA score >= 0.85."""
    analyzer = ELAAnalyzer()

    # Create uniform image with some text/gradients
    img = Image.new("RGB", (600, 600), color=(240, 240, 245))
    test_file = tmp_path / "pristine.jpg"
    img.save(test_file, format="JPEG", quality=90)

    ela_map, score, bboxes, pix_bboxes = analyzer.analyze(test_file)

    assert score >= 0.85
    assert len(bboxes) == 0
    assert ela_map.shape == (600, 600, 3)


def test_detects_spliced_jpeg_box(tmp_path: Path):
    """TC-FOR-01: Detect ELA compression inconsistency when a foreign JPEG patch is spliced."""
    analyzer = ELAAnalyzer()

    # Base image saved at quality 60
    base_img = Image.new("RGB", (600, 600), color=(230, 230, 230))
    # Draw some varied background lines
    base_arr = np.array(base_img)
    base_arr[::10, :] = 200
    base_img = Image.fromarray(base_arr)

    base_file = tmp_path / "base.jpg"
    base_img.save(base_file, format="JPEG", quality=60)

    # Patch image saved at quality 98 with high contrast
    patch = Image.new("RGB", (120, 120), color=(255, 255, 255))
    patch_arr = np.array(patch)
    patch_arr[::4, ::4] = (0, 0, 150)
    patch = Image.fromarray(patch_arr)

    patch_buffer = io.BytesIO()
    patch.save(patch_buffer, format="JPEG", quality=98)
    patch_buffer.seek(0)
    patch_reloaded = Image.open(patch_buffer)

    # Splice patch into base image at (200, 200)
    spliced = Image.open(base_file).copy()
    spliced.paste(patch_reloaded, (200, 200))
    spliced_file = tmp_path / "spliced.jpg"
    spliced.save(spliced_file, format="JPEG", quality=60)

    ela_map, score, bboxes, pix_bboxes = analyzer.analyze(spliced_file)

    assert score < 0.85
    assert len(pix_bboxes) >= 1

    # Verify at least one bounding box encompasses the spliced patch area around (200, 200)
    found_splice = any((150 <= pb.x <= 250) and (150 <= pb.y <= 250) for pb in pix_bboxes)
    assert found_splice


def test_multi_quality_ela_curve(tmp_path: Path):
    """Verify ELA error curve and estimated original quality factor."""
    analyzer = ELAAnalyzer()

    img = Image.new("RGB", (400, 400), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 350], fill=(100, 150, 200), outline=(10, 20, 30))
    draw.ellipse([100, 100, 300, 300], fill=(220, 180, 50))
    test_file = tmp_path / "curve_test.jpg"
    img.save(test_file, format="JPEG", quality=85)

    res = analyzer.multi_quality_ela_curve(test_file, qualities=[75, 85, 95])

    assert "error_curve" in res
    assert len(res["error_curve"]) == 3
    assert res["estimated_original_quality"] == 85
