from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from app.modules.preprocessing.base_step import BasePreprocessingStep
from app.modules.preprocessing.color_conversion import to_grayscale


def order_points(pts: np.ndarray) -> np.ndarray:
    """Order 4 (x, y) coordinates consistently: top-left, top-right, bottom-right, bottom-left."""
    rect = np.zeros((4, 2), dtype="float32")

    # Sum of coordinates: Top-left has smallest sum, bottom-right has largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Difference of coordinates: Top-right has smallest diff (x - y is largest / y - x is smallest)
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Extract and rectify a 4-point quadrilateral into an orthogonal rectangle."""
    rect = order_points(pts)
    tl, tr, br, bl = rect

    # Compute width of new image
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_width = max(int(width_a), int(width_b))

    # Compute height of new image
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_height = max(int(height_a), int(height_b))

    # Guard against invalid collapsed geometries
    if max_width < 100 or max_height < 100:
        return image

    dst = np.array(
        [
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1],
        ],
        dtype="float32",
    )

    m = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, m, (max_width, max_height), flags=cv2.INTER_CUBIC)


def find_document_corners(image: np.ndarray, min_area_ratio: float = 0.25) -> Optional[np.ndarray]:
    """Locate the 4 corners of a rectangular certificate document in an image."""
    h, w = image.shape[:2]

    # Downscale for fast and robust edge detection
    target_w = 800.0
    scale = target_w / float(w) if w > target_w else 1.0
    scaled_w = int(w * scale)
    scaled_h = int(h * scale)

    resized = cv2.resize(image, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
    gray = to_grayscale(resized)

    # Blur and detect edges
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 180)

    # Dilate edges slightly to close small contour gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    for c in contours:
        area = cv2.contourArea(c)
        # Check area against scaled total area
        if area < (min_area_ratio * scaled_w * scaled_h):
            continue

        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4 and cv2.isContourConvex(approx):
            # Scale coordinates back up to original image resolution
            orig_pts = approx.reshape(4, 2).astype("float32") / scale
            return orig_pts

    return None


class PerspectiveWarper(BasePreprocessingStep):
    """Detects document boundary corners and rectifies perspective distortion."""

    def __init__(self, enabled: bool = True, min_area_ratio: float = 0.25):
        self.enabled = enabled
        self.min_area_ratio = min_area_ratio

    @property
    def name(self) -> str:
        return "PerspectiveWarper"

    def process(
        self, image: np.ndarray, context: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        if not self.enabled:
            context["perspective_corrected"] = False
            return image, context

        corners = find_document_corners(image, min_area_ratio=self.min_area_ratio)

        if corners is not None:
            rectified = four_point_transform(image, corners)
            context["perspective_corrected"] = True
            context["detected_corners"] = corners.tolist()
            return rectified, context

        context["perspective_corrected"] = False
        return image, context
