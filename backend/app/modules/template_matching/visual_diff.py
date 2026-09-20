from pathlib import Path
from typing import Optional

import cv2
import numpy as np


def generate_visual_diff(
    aligned_img: np.ndarray,
    template_img: np.ndarray,
    ssim_diff_map: np.ndarray,
    output_path: Optional[str] = None,
) -> np.ndarray:
    """Generate a composite panel: [ Master Template | Query Certificate | SSIM Heatmap ].

    Args:
        aligned_img: Aligned query certificate image.
        template_img: Reference master template image.
        ssim_diff_map: Normalized SSIM difference map uint8 (0 = identical, 255 = max difference).
        output_path: Optional path to save composite image to disk.

    Returns:
        3-panel composite image array.
    """
    target_h, target_w = 600, 800

    def prepare_panel(img: np.ndarray, label: str) -> np.ndarray:
        if img.ndim == 2:
            bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            bgr = img.copy()
        resized = cv2.resize(bgr, (target_w, target_h), interpolation=cv2.INTER_AREA)

        # Header banner for label
        banner = np.zeros((40, target_w, 3), dtype=np.uint8)
        cv2.putText(
            banner,
            label,
            (15, 26),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        return np.vstack([banner, resized])

    # Generate color heatmap from difference map
    heatmap_colored = cv2.applyColorMap(ssim_diff_map, cv2.COLORMAP_JET)

    panel_tpl = prepare_panel(template_img, "Master Template (Reference)")
    panel_query = prepare_panel(aligned_img, "Query Certificate (Aligned)")
    panel_diff = prepare_panel(heatmap_colored, "Structural Divergence Heatmap")

    composite = np.hstack([panel_tpl, panel_query, panel_diff])

    if output_path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(p), composite)

    return composite
