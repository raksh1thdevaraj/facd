from typing import Any, Dict, Tuple, Union

import cv2
import numpy as np

from app.schemas.template_matching import SealROI


def match_seal_and_logo(
    aligned_img: np.ndarray,
    template_img: np.ndarray,
    seal_roi: Union[SealROI, Dict[str, Any]],
    search_padding_px: int = 15,
) -> Tuple[float, float, float]:
    """Extract university seal/logo ROI and evaluate geometric & color consistency.

    Args:
        aligned_img: Aligned certificate image array.
        template_img: Reference master template image array.
        seal_roi: Bounding box coordinates {x, y, width, height}.
        search_padding_px: Pixel margin around ROI to tolerate residual micro-shifts.

    Returns:
        Tuple of (composite_seal_score, cross_correlation_max, color_histogram_corr).
    """
    if aligned_img is None or template_img is None:
        raise ValueError("aligned_img and template_img cannot be None.")

    # Parse ROI coordinates
    if isinstance(seal_roi, SealROI):
        x, y, w, h = seal_roi.x, seal_roi.y, seal_roi.width, seal_roi.height
    elif isinstance(seal_roi, dict):
        x = int(seal_roi.get("x", 0))
        y = int(seal_roi.get("y", 0))
        w = int(seal_roi.get("width", seal_roi.get("w", 0)))
        h = int(seal_roi.get("height", seal_roi.get("h", 0)))
    else:
        return 0.0, 0.0, 0.0

    img_h, img_w = template_img.shape[:2]

    # Validate bounding box coordinates
    if w <= 10 or h <= 10 or x < 0 or y < 0 or x + w > img_w or y + h > img_h:
        return 0.0, 0.0, 0.0

    # Crop master template seal
    template_seal = template_img[y : y + h, x : x + w]
    if template_seal.size == 0:
        return 0.0, 0.0, 0.0

    # Crop query image seal with slight search padding
    pad_y1 = max(0, y - search_padding_px)
    pad_y2 = min(aligned_img.shape[0], y + h + search_padding_px)
    pad_x1 = max(0, x - search_padding_px)
    pad_x2 = min(aligned_img.shape[1], x + w + search_padding_px)

    query_search_area = aligned_img[pad_y1:pad_y2, pad_x1:pad_x2]
    query_exact_seal = aligned_img[y : y + h, x : x + w]

    if query_search_area.shape[0] < h or query_search_area.shape[1] < w:
        return 0.0, 0.0, 0.0

    # 1. Multi-scale / Normalized Cross-Correlation Template Matching
    if template_seal.ndim == 3 and query_search_area.ndim == 3:
        tpl_gray = cv2.cvtColor(template_seal, cv2.COLOR_BGR2GRAY)
        query_gray = cv2.cvtColor(query_search_area, cv2.COLOR_BGR2GRAY)
    else:
        tpl_gray = template_seal
        query_gray = query_search_area

    match_res = cv2.matchTemplate(query_gray, tpl_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(match_res)
    r_max = float(max(0.0, max_val))

    # 2. 2D Hue-Saturation Color Histogram Correlation
    if (
        template_seal.ndim == 3
        and query_exact_seal.ndim == 3
        and query_exact_seal.shape == template_seal.shape
    ):
        tpl_hsv = cv2.cvtColor(template_seal, cv2.COLOR_BGR2HSV)
        query_hsv = cv2.cvtColor(query_exact_seal, cv2.COLOR_BGR2HSV)

        # 50 Hue bins, 60 Saturation bins
        hist_tpl = cv2.calcHist([tpl_hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        hist_query = cv2.calcHist([query_hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])

        cv2.normalize(hist_tpl, hist_tpl, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist_query, hist_query, 0, 1, cv2.NORM_MINMAX)

        hist_corr = float(cv2.compareHist(hist_tpl, hist_query, cv2.HISTCMP_CORREL))
        hist_corr = max(0.0, min(1.0, hist_corr))
    else:
        hist_corr = r_max

    # 3. Composite Score: 65% geometric cross-correlation, 35% color distribution
    composite_score = float(np.clip(0.65 * r_max + 0.35 * hist_corr, 0.0, 1.0))

    return round(composite_score, 4), round(r_max, 4), round(hist_corr, 4)
