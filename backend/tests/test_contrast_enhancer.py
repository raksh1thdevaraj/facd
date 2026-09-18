import cv2
import numpy as np

from app.modules.preprocessing.contrast_enhancer import CLAHEEnhancer


def test_clahe_enhances_low_contrast_image():
    # Low-contrast image (narrow dynamic range between 100 and 140)
    low_contrast = np.linspace(100, 140, 600 * 800, dtype=np.uint8).reshape((600, 800))
    # Add faint text
    cv2.putText(
        low_contrast,
        "University of Excellence",
        (150, 300),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.5,
        105,
        2,
    )

    std_before = np.std(low_contrast)

    enhancer = CLAHEEnhancer(clip_limit=3.0, tile_grid_size=(8, 8))
    enhanced, ctx = enhancer.process(low_contrast, {})

    std_after = np.std(enhanced)
    assert std_after > std_before
    assert ctx["contrast_applied"] is True
    assert ctx["contrast_ratio"] > 1.0


def test_clahe_on_color_certificate():
    # 3-channel BGR certificate with non-uniform lighting gradient
    h, w = 600, 800
    y, x = np.mgrid[0:h, 0:w]
    # Vignette shadow gradient: center bright, corners darker
    radius = np.sqrt((x - w / 2) ** 2 + (y - h / 2) ** 2)
    shadow = np.clip(220 - (radius / 3.0), 80, 220).astype(np.uint8)

    color_img = cv2.merge([shadow, shadow, shadow])
    cv2.putText(
        color_img,
        "Academic Certificate",
        (150, 300),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 0, 180),
        2,
    )

    enhancer = CLAHEEnhancer(clip_limit=2.0)
    enhanced, ctx = enhancer.process(color_img, {})

    assert enhanced.shape == (600, 800, 3)
    assert ctx["contrast_applied"] is True
    assert not np.array_equal(enhanced, color_img)
