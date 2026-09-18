import logging
from typing import Dict, List, Optional

from app.modules.ocr.base_engine import BaseOCREngine
from app.modules.ocr.easyocr_engine import EasyOCREngine
from app.modules.ocr.mock_engine import MockOCREngine
from app.modules.ocr.tesseract_engine import TesseractOCREngine

logger = logging.getLogger(__name__)


class EngineFactory:
    """Factory for selecting and instantiating OCR engines with graceful degradation."""

    @classmethod
    def get_engine(
        cls,
        engine_name: Optional[str] = "auto",
        languages: Optional[List[str]] = None,
        gpu: bool = False,
    ) -> BaseOCREngine:
        """Create or retrieve the requested OCR engine with automatic fallback."""
        name = (engine_name or "auto").lower()

        if name == "mock":
            return MockOCREngine()

        if name == "pytesseract":
            tess = TesseractOCREngine()
            if tess.is_available:
                return tess
            logger.warning("PyTesseract requested but unavailable, falling back to EasyOCR.")

        if name in ("easyocr", "auto", "paddleocr"):
            try:
                easy = EasyOCREngine(languages=languages, gpu=gpu)
                if easy.is_available:
                    return easy
            except Exception as exc:
                logger.warning("Failed to initialize EasyOCREngine: %s", exc)

        # Fallback to Tesseract if EasyOCR failed
        tess = TesseractOCREngine()
        if tess.is_available:
            logger.info("Falling back to PyTesseract engine.")
            return tess

        # Final fallback to Mock engine
        logger.warning(
            "No physical OCR engine available on this system. Falling back to MockOCREngine."
        )
        return MockOCREngine()

    @classmethod
    def get_available_engines(cls) -> Dict[str, bool]:
        """Query availability status for all known OCR backends."""
        tess_avail = TesseractOCREngine().is_available
        try:
            easy_avail = EasyOCREngine().is_available
        except Exception:
            easy_avail = False

        return {
            "easyocr": easy_avail,
            "pytesseract": tess_avail,
            "mock": True,
        }
