import numpy as np

from app.modules.forensics.noise_analyzer import NoiseAnalyzer


def test_uniform_noise_clean_score():
    """Verify that an image with uniform background noise yields noise score >= 0.90."""
    analyzer = NoiseAnalyzer()

    # Create uniform image with slight natural background variation
    base = np.full((600, 600), 240, dtype=np.uint8)
    noise = np.random.normal(0, 2.0, (600, 600)).astype(np.int16)
    noisy_img = np.clip(base.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    noise_map, score, bboxes, pix_bboxes = analyzer.analyze(noisy_img)

    assert score >= 0.90
    assert len(bboxes) == 0
    assert noise_map.shape == (600, 600)


def test_detects_noise_variance_inconsistency():
    """TC-FOR-03: Detect sensor noise variance anomaly when a high-noise patch is spliced."""
    analyzer = NoiseAnalyzer()

    # Clean flatbed scan background with low noise (sigma=1.0)
    img = np.full((600, 600), 235, dtype=np.uint8)
    clean_noise = np.random.normal(0, 1.0, (600, 600)).astype(np.int16)
    canvas = np.clip(img.astype(np.int16) + clean_noise, 0, 255).astype(np.uint8)

    # Splice high-noise foreign patch (sigma=25.0) at (200:320, 200:320)
    high_noise = np.random.normal(0, 25.0, (120, 120)).astype(np.int16)
    patch = np.clip(235 + high_noise, 0, 255).astype(np.uint8)
    canvas[200:320, 200:320] = patch

    noise_map, score, bboxes, pix_bboxes = analyzer.analyze(canvas)

    assert score < 0.85
    assert len(pix_bboxes) >= 1

    # Verify at least one bounding box overlaps the high-noise region
    found = any((160 <= pb.x <= 260) and (160 <= pb.y <= 260) for pb in pix_bboxes)
    assert found


def test_empty_or_small_image_handled_gracefully():
    """Verify small or empty images do not raise exceptions."""
    analyzer = NoiseAnalyzer()

    empty = np.zeros((0, 0), dtype=np.uint8)
    _, score_empty, bboxes_empty, _ = analyzer.analyze(empty)
    assert score_empty == 1.0
    assert len(bboxes_empty) == 0
