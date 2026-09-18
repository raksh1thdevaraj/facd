from typing import Any, Dict, Literal, Tuple

import cv2
import numpy as np

from app.modules.preprocessing.base_step import BasePreprocessingStep


class NoiseReductionFilter(BasePreprocessingStep):
    """Edge-preserving noise reduction filter (Bilateral or Median)."""

    def __init__(
        self,
        filter_type: Literal["bilateral", "median", "none"] = "bilateral",
        d: int = 9,
        sigma_color: float = 75.0,
        sigma_space: float = 75.0,
        median_ksize: int = 3,
    ):
        self.filter_type = filter_type
        self.d = d
        self.sigma_color = sigma_color
        self.sigma_space = sigma_space
        self.median_ksize = median_ksize

    @property
    def name(self) -> str:
        return f"NoiseReductionFilter({self.filter_type})"

    def process(
        self, image: np.ndarray, context: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        if self.filter_type == "none":
            context["noise_reduction_applied"] = False
            return image, context

        if self.filter_type == "bilateral":
            # Bilateral filter preserves sharp character edges while smoothing paper grain
            if image.ndim == 2:
                denoised = cv2.bilateralFilter(
                    image, d=self.d, sigmaColor=self.sigma_color, sigmaSpace=self.sigma_space
                )
            else:
                denoised = cv2.bilateralFilter(
                    image, d=self.d, sigmaColor=self.sigma_color, sigmaSpace=self.sigma_space
                )
            context["noise_reduction_applied"] = True
            return denoised, context

        elif self.filter_type == "median":
            denoised = cv2.medianBlur(image, ksize=self.median_ksize)
            context["noise_reduction_applied"] = True
            return denoised, context

        return image, context
