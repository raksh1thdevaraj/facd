import cv2
import numpy as np

from app.modules.preprocessing.binarizer import AdaptiveBinarizer


def create_document_with_text() -> np.ndarray:
    """Create a white document with crisp black text and background noise."""
    doc = np.ones((600, 800), dtype=np.uint8) * 245

    # Draw dark text
    cv2.putText(
        doc,
        "OFFICIAL TRANSCRIPT OF RECORDS",
        (100, 200),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        30,
        2,
    )
    cv2.putText(
        doc,
        "Student Registration No: 2024-ENG-0891",
        (100, 300),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        30,
        2,
    )

    # Add minor background salt-and-pepper noise
    noise = np.random.randint(0, 255, (600, 800), dtype=np.uint8)
    doc[noise > 250] = 50
    return doc


def test_adaptive_binarization_polarity():
    doc = create_document_with_text()
    binarizer = AdaptiveBinarizer(method="adaptive_gaussian", block_size=21, c=11.0)
    binary, ctx = binarizer.process(doc, {})

    assert binary.ndim == 2
    assert binary.dtype == np.uint8

    unique_vals = set(np.unique(binary))
    assert unique_vals.issubset({0, 255})

    # In a text document, background (255) must occupy > 70% of total area
    white_fraction = np.sum(binary == 255) / float(binary.size)
    assert white_fraction > 0.70

    # The text region must contain black pixels (0)
    text_pixel_count = np.sum(binary[180:220, 100:500] == 0)
    assert text_pixel_count > 100


def test_otsu_binarization():
    doc = create_document_with_text()
    binarizer = AdaptiveBinarizer(method="otsu")
    binary, ctx = binarizer.process(doc, {})

    assert binary.ndim == 2
    assert binary.dtype == np.uint8
    white_fraction = np.sum(binary == 255) / float(binary.size)
    assert white_fraction > 0.70
