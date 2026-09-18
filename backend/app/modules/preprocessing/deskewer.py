from typing import Any, Dict, Tuple

import cv2
import numpy as np

from app.modules.preprocessing.base_step import BasePreprocessingStep
from app.modules.preprocessing.color_conversion import to_grayscale


def estimate_skew_angle(
    gray_image: np.ndarray,
    max_angle: float = 45.0,
    min_threshold: float = 0.2,
) -> float:
    """Detect document tilt angle within [-max_angle, +max_angle] degrees.

    Uses probabilistic Hough line transform on text baselines, with
    minimum-area bounding rectangle as fallback.
    """
    h, w = gray_image.shape[:2]

    # 1. Detect candidate horizontal text lines using HoughLinesP
    edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=80,
        minLineLength=int(w * 0.1),
        maxLineGap=15,
    )

    angles = []
    if lines is not None:
        for line in lines:
            coords = line.flatten()
            if len(coords) < 4:
                continue
            x1, y1, x2, y2 = coords[:4]
            dx = x2 - x1
            dy = y2 - y1
            if dx == 0:
                continue
            deg = np.degrees(np.arctan2(dy, dx))
            if abs(deg) <= max_angle:
                angles.append(deg)

    if len(angles) >= 3:
        median_angle = float(np.median(angles))
        if abs(median_angle) >= min_threshold:
            return median_angle

    # 2. Fallback: MinAreaRect of thresholded text pixels
    thresh = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    pts = np.column_stack(np.where(thresh > 0))
    if len(pts) < 100:
        return 0.0

    rect = cv2.minAreaRect(pts)
    rect_angle = rect[-1]

    # OpenCV minAreaRect normalization
    if rect_angle < -45.0:
        angle = -(90.0 + rect_angle)
    elif rect_angle > 45.0:
        angle = 90.0 - rect_angle
    else:
        angle = -rect_angle

    if abs(angle) > max_angle or abs(angle) < min_threshold:
        return 0.0

    return float(angle)


def rotate_image(
    image: np.ndarray, angle: float, border_color: Tuple[int, int, int] = (255, 255, 255)
) -> np.ndarray:
    """Rotate image by angle (in degrees) around center, expanding canvas to prevent clipping."""
    if abs(angle) < 1e-3:
        return image.copy()

    h, w = image.shape[:2]
    cx, cy = w / 2.0, h / 2.0

    # Note: cv2.getRotationMatrix2D uses positive angle for counter-clockwise rotation.
    # To correct a clockwise tilt of theta, we rotate by -theta.
    m = cv2.getRotationMatrix2D((cx, cy), -angle, 1.0)

    cos_val = np.abs(m[0, 0])
    sin_val = np.abs(m[0, 1])

    new_w = int((h * sin_val) + (w * cos_val))
    new_h = int((h * cos_val) + (w * sin_val))

    m[0, 2] += (new_w / 2.0) - cx
    m[1, 2] += (new_h / 2.0) - cy

    fill_val = 255 if image.ndim == 2 else border_color

    return cv2.warpAffine(
        image,
        m,
        (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=fill_val,
    )


class Deskewer(BasePreprocessingStep):
    """Detects rotational skew and deskews certificate images."""

    def __init__(
        self,
        enabled: bool = True,
        max_angle: float = 45.0,
        min_threshold: float = 0.2,
    ):
        self.enabled = enabled
        self.max_angle = max_angle
        self.min_threshold = min_threshold

    @property
    def name(self) -> str:
        return "Deskewer"

    def process(
        self, image: np.ndarray, context: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        if not self.enabled:
            context["applied_skew_angle"] = 0.0
            return image, context

        gray = to_grayscale(image)
        detected_angle = estimate_skew_angle(
            gray,
            max_angle=self.max_angle,
            min_threshold=self.min_threshold,
        )

        if abs(detected_angle) >= self.min_threshold:
            rotated = rotate_image(image, -detected_angle)
            context["applied_skew_angle"] = detected_angle
            return rotated, context

        context["applied_skew_angle"] = 0.0
        return image, context
