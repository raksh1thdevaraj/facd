import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional, Union

import cv2
import numpy as np

from app.modules.ocr.base_engine import BaseOCREngine
from app.modules.ocr.token_builder import TokenBuilder
from app.schemas.pipeline import OCRToken

logger = logging.getLogger(__name__)


class TesseractOCREngine(BaseOCREngine):
    """OCR engine wrapper around PyTesseract with graceful binary discovery."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        self._cmd = tesseract_cmd or os.getenv("TESSERACT_CMD")
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if pytesseract and tesseract executable are present on the system."""
        try:
            import pytesseract

            if self._cmd:
                pytesseract.pytesseract.tesseract_cmd = self._cmd

            cmd_to_check = self._cmd or "tesseract"
            if shutil.which(cmd_to_check) is not None or (self._cmd and Path(self._cmd).exists()):
                return True

            # Try running version
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    @property
    def engine_name(self) -> str:
        return "pytesseract"

    @property
    def is_available(self) -> bool:
        return self._available

    def extract_tokens(
        self,
        image_or_path: Union[np.ndarray, Path, str],
    ) -> List[OCRToken]:
        """Extract OCR tokens using PyTesseract."""
        if not self._available:
            raise RuntimeError("PyTesseract binary is not installed or not found on PATH.")

        import pytesseract
        from pytesseract import Output

        if isinstance(image_or_path, (str, Path)):
            path = Path(image_or_path)
            img = cv2.imread(str(path))
            if img is None:
                raise ValueError(f"Unable to read image at: {path}")
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img_h, img_w = img_rgb.shape[:2]
        elif isinstance(image_or_path, np.ndarray):
            img_h, img_w = image_or_path.shape[:2]
            if len(image_or_path.shape) == 2:
                img_rgb = cv2.cvtColor(image_or_path, cv2.COLOR_GRAY2RGB)
            elif image_or_path.shape[2] == 4:
                img_rgb = cv2.cvtColor(image_or_path, cv2.COLOR_BGRA2RGB)
            else:
                img_rgb = cv2.cvtColor(image_or_path, cv2.COLOR_BGR2RGB)
        else:
            raise TypeError(f"Unsupported image type: {type(image_or_path)}")

        data = pytesseract.image_to_data(img_rgb, output_type=Output.DICT)
        return TokenBuilder.from_tesseract_data(data, img_w, img_h)
