from typing import Tuple

import cv2
import numpy as np


def normalize_resolution(
    image: np.ndarray,
    min_long_edge: int = 1200,
    max_long_edge: int = 3200,
) -> Tuple[np.ndarray, float]:
    """Standardize image dimensions within [min_long_edge, max_long_edge] preserving aspect ratio.

    Returns:
        Tuple of (resized_image, scale_factor).
    """
    h, w = image.shape[:2]
    long_edge = max(w, h)

    if long_edge > max_long_edge:
        scale = float(max_long_edge) / float(long_edge)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return resized, scale

    if long_edge < min_long_edge:
        scale = float(min_long_edge) / float(long_edge)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        return resized, scale

    return image.copy(), 1.0


def create_thumbnail(image: np.ndarray, max_edge: int = 400) -> np.ndarray:
    """Generate a lightweight web thumbnail preview preserving aspect ratio."""
    h, w = image.shape[:2]
    long_edge = max(w, h)

    if long_edge <= max_edge:
        return image.copy()

    scale = float(max_edge) / float(long_edge)
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
