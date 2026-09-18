from typing import Any, Dict, Literal, Tuple

import cv2
import numpy as np

from app.modules.preprocessing.base_step import BasePreprocessingStep
from app.modules.preprocessing.color_conversion import to_grayscale


class AdaptiveBinarizer(BasePreprocessingStep):
    """Binarizes certificate image into crisp black-and-white for OCR ingestion."""

    def __init__(
        self,
        method: Literal["adaptive_gaussian", "otsu"] = "adaptive_gaussian",
        block_size: int = 21,
        c: float = 11.0,
    ):
        self.method = method
        self.block_size = block_size if block_size % 2 == 1 else block_size + 1
        self.c = c

    @property
    def name(self) -> str:
        return f"AdaptiveBinarizer({self.method})"

    def process(
        self, image: np.ndarray, context: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        gray = to_grayscale(image)

        if self.method == "otsu":
            # Otsu automatic global threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            # Adaptive Gaussian local threshold
            binary = cv2.adaptiveThreshold(
                gray,
                maxValue=255,
                adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                thresholdType=cv2.THRESH_BINARY,
                blockSize=self.block_size,
                C=self.c,
            )

        # Polarity check: text must be black (0), background must be white (255)
        # In a standard document, majority of pixels are white background (> 50%)
        mean_val = float(np.mean(binary))
        if mean_val < 127.0:
            binary = cv2.bitwise_not(binary)

        # Remove isolated background speckles with subtle 2x2 morphological opening
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        context["binarization_mean_intensity"] = mean_val
        return binary, context
