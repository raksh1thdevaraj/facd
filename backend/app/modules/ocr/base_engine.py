from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union

import numpy as np

from app.schemas.pipeline import OCRToken


class BaseOCREngine(ABC):
    """Abstract interface defining the OCR detection and character recognition contract."""

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Name of the OCR engine backend (e.g., 'easyocr', 'pytesseract', 'mock')."""
        pass

    @abstractmethod
    def extract_tokens(
        self,
        image_or_path: Union[np.ndarray, Path, str],
    ) -> List[OCRToken]:
        """Extract OCR tokens with bounding boxes and confidence scores from an image."""
        pass
