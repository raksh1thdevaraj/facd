import logging
import threading
from pathlib import Path
from typing import List, Optional, Sequence, Union

import cv2
import numpy as np

from app.modules.ocr.base_engine import BaseOCREngine
from app.modules.ocr.token_builder import TokenBuilder
from app.schemas.pipeline import OCRToken

logger = logging.getLogger(__name__)


class EasyOCREngine(BaseOCREngine):
    """Thread-safe singleton OCR engine wrapper around EasyOCR."""

    _instance: Optional["EasyOCREngine"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs) -> "EasyOCREngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        languages: Optional[Sequence[str]] = None,
        gpu: bool = False,
    ):
        if getattr(self, "_initialized", False):
            return

        self.languages = list(languages or ["en"])
        self.gpu = gpu
        self._reader = None
        self._reader_lock = threading.Lock()
        self._initialize_reader()
        self._initialized = True

    def _initialize_reader(self) -> None:
        """Initialize EasyOCR Reader with CPU/GPU safety."""
        try:
            import easyocr
            import torch

            # Rule 5.1: Graceful fallback when GPU unavailable
            use_gpu = self.gpu and torch.cuda.is_available()
            logger.info(
                "Initializing EasyOCR (languages=%s, gpu=%s, torch_device=%s)",
                self.languages,
                use_gpu,
                "cuda" if use_gpu else "cpu",
            )
            self._reader = easyocr.Reader(
                self.languages,
                gpu=use_gpu,
                verbose=False,
            )
            logger.info("EasyOCR Reader successfully initialized.")
        except Exception as exc:
            logger.warning("Failed to initialize EasyOCR Reader: %s", exc)
            self._reader = None

    @property
    def engine_name(self) -> str:
        return "easyocr"

    @property
    def is_available(self) -> bool:
        return self._reader is not None

    def extract_tokens(
        self,
        image_or_path: Union[np.ndarray, Path, str],
    ) -> List[OCRToken]:
        """Extract OCR tokens using EasyOCR."""
        if self._reader is None:
            raise RuntimeError("EasyOCR engine is not initialized or unavailable.")

        # Resolve image and dimensions
        if isinstance(image_or_path, (str, Path)):
            path = Path(image_or_path)
            if not path.exists():
                raise FileNotFoundError(f"Image not found at: {path}")
            img_bgr = cv2.imread(str(path))
            if img_bgr is None:
                raise ValueError(f"Unable to read image at: {path}")
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
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

        with self._reader_lock:
            raw_results = self._reader.readtext(img_rgb)

        return TokenBuilder.from_easyocr_result(raw_results, img_w, img_h)
