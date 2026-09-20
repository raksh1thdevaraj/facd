from typing import Optional, Tuple

import cv2
import numpy as np
from skimage.metrics import structural_similarity


def compute_template_ssim(
    aligned_img: np.ndarray,
    template_img: np.ndarray,
    variable_mask: Optional[np.ndarray] = None,
) -> Tuple[float, np.ndarray]:
    """Compute global and masked Structural Similarity Index (SSIM) against master template.

    Args:
        aligned_img: Aligned certificate image array (BGR or grayscale).
        template_img: Master reference template image array.
        variable_mask: Optional binary mask (0 = invariant layout, 1 = variable text).

    Returns:
        Tuple of (ssim_score, ssim_diff_map_normalized).
    """
    if aligned_img is None or template_img is None:
        raise ValueError("aligned_img and template_img must not be None.")

    h_tpl, w_tpl = template_img.shape[:2]

    # Resize aligned image if dimensions differ
    if aligned_img.shape[:2] != (h_tpl, w_tpl):
        aligned_img = cv2.resize(aligned_img, (w_tpl, h_tpl), interpolation=cv2.INTER_LINEAR)

    # Convert to grayscale
    aligned_gray = (
        cv2.cvtColor(aligned_img, cv2.COLOR_BGR2GRAY) if aligned_img.ndim == 3 else aligned_img
    )
    template_gray = (
        cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY) if template_img.ndim == 3 else template_img
    )

    # Calculate full SSIM diff map
    score, diff = structural_similarity(
        template_gray,
        aligned_gray,
        channel_axis=None,
        full=True,
        gaussian_weights=True,
        sigma=1.5,
        data_range=255.0,
    )

    # If variable mask provided, exclude variable text regions from score calculation
    if variable_mask is not None:
        if variable_mask.shape[:2] != (h_tpl, w_tpl):
            variable_mask = cv2.resize(
                variable_mask.astype(np.uint8), (w_tpl, h_tpl), interpolation=cv2.INTER_NEAREST
            )
        invariant_pixels = variable_mask == 0
        if np.any(invariant_pixels):
            score = float(np.mean(diff[invariant_pixels]))

    # Normalize diff map for visual inspection: values range [-1, 1] -> map to [0, 255] uint8
    # 0 = identical (high similarity), 255 = maximum divergence
    diff_normalized = np.clip((1.0 - (diff + 1.0) / 2.0) * 255.0, 0, 255).astype(np.uint8)

    return float(np.clip(score, 0.0, 1.0)), diff_normalized


def evaluate_ssim_category(ssim_score: float) -> str:
    """Categorize SSIM score into genuine, suspicious, or counterfeit."""
    if ssim_score >= 0.85:
        return "GENUINE_LAYOUT"
    elif ssim_score >= 0.60:
        return "SUSPICIOUS_LAYOUT"
    else:
        return "COUNTERFEIT_LAYOUT"
