from typing import Any, Dict, Tuple

import cv2
import numpy as np

from app.modules.preprocessing.base_step import BasePreprocessingStep
from app.modules.preprocessing.color_conversion import ensure_3channel


class CLAHEEnhancer(BasePreprocessingStep):
    """Contrast Limited Adaptive Histogram Equalization applied to the luminance channel."""

    def __init__(
        self,
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8),
        enabled: bool = True,
    ):
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
        self.enabled = enabled

    @property
    def name(self) -> str:
        return f"CLAHEEnhancer(clip={self.clip_limit})"

    def process(
        self, image: np.ndarray, context: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        if not self.enabled:
            context["contrast_applied"] = False
            return image, context

        clahe = cv2.createCLAHE(
            clipLimit=self.clip_limit,
            tileGridSize=self.tile_grid_size,
        )

        std_before = float(np.std(image))

        if image.ndim == 2:
            enhanced = clahe.apply(image)
        else:
            bgr = ensure_3channel(image)
            lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
            l_chan, a_chan, b_chan = cv2.split(lab)
            enhanced_l = clahe.apply(l_chan)
            merged_lab = cv2.merge([enhanced_l, a_chan, b_chan])
            enhanced = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)

        std_after = float(np.std(enhanced))
        context["contrast_applied"] = True
        context["contrast_std_before"] = std_before
        context["contrast_std_after"] = std_after
        context["contrast_ratio"] = std_after / (std_before + 1e-6)

        return enhanced, context
