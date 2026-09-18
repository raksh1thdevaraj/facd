from pathlib import Path
from typing import List, Optional, Union

import cv2
import numpy as np

from app.modules.ocr.base_engine import BaseOCREngine
from app.modules.ocr.token_builder import TokenBuilder
from app.schemas.pipeline import OCRToken


class MockOCREngine(BaseOCREngine):
    """Deterministic mock OCR engine for rapid unit tests and offline testing."""

    def __init__(
        self,
        canned_tokens: Optional[List[OCRToken]] = None,
        default_confidence: float = 0.95,
    ):
        self._canned_tokens = canned_tokens
        self.default_confidence = default_confidence

    @property
    def engine_name(self) -> str:
        return "mock"

    def set_tokens(self, tokens: List[OCRToken]) -> None:
        """Explicitly set tokens to return on subsequent extract calls."""
        self._canned_tokens = tokens

    def extract_tokens(
        self,
        image_or_path: Union[np.ndarray, Path, str],
    ) -> List[OCRToken]:
        """Return configured tokens, or generate synthetic academic certificate tokens."""
        if self._canned_tokens is not None:
            return list(self._canned_tokens)

        # Resolve image dimensions
        img_w, img_h = 1600, 1200
        if isinstance(image_or_path, np.ndarray):
            img_h, img_w = image_or_path.shape[:2]
        elif isinstance(image_or_path, (str, Path)):
            path = Path(image_or_path)
            if path.exists():
                img = cv2.imread(str(path))
                if img is not None:
                    img_h, img_w = img.shape[:2]

        return self.create_synthetic_certificate_tokens(img_w, img_h)

    def create_synthetic_certificate_tokens(
        self,
        img_w: int,
        img_h: int,
        student_name: str = "RAKSHITH DEVARAJA",
        roll_no: str = "1MS20CS001",
        degree: str = "Bachelor of Technology in Computer Science and Engineering",
        institution: str = "VISVESVARAYA TECHNOLOGICAL UNIVERSITY",
        issue_date: str = "15th June 2024",
        grade: str = "CGPA: 9.45 / 10.0 (First Class with Distinction)",
        cert_id: str = "VTU-2024-889921",
        confidence: Optional[float] = None,
    ) -> List[OCRToken]:
        """Generate a realistic set of academic certificate OCR tokens."""
        conf = confidence if confidence is not None else self.default_confidence
        tokens: List[OCRToken] = []

        lines_spec = [
            # Line 0: Institution
            (institution, int(img_h * 0.12)),
            # Line 1: Subheader
            ("BELAGAVI, KARNATAKA, INDIA", int(img_h * 0.18)),
            # Line 2: Degree title header
            ("THIS IS TO CERTIFY THAT", int(img_h * 0.30)),
            # Line 3: Student name
            (student_name, int(img_h * 0.38)),
            # Line 4: Roll no
            (f"USN: {roll_no}", int(img_h * 0.46)),
            # Line 5: Degree
            (f"HAS BEEN CONFERRED THE DEGREE OF {degree}", int(img_h * 0.54)),
            # Line 6: Grade
            (f"ACADEMIC PERFORMANCE: {grade}", int(img_h * 0.62)),
            # Line 7: Issue Date
            (f"GIVEN UNDER THE SEAL OF THE UNIVERSITY ON {issue_date}", int(img_h * 0.75)),
            # Line 8: Serial Number
            (f"CERTIFICATE NO: {cert_id}", int(img_h * 0.88)),
        ]

        for text_line, y_pos in lines_spec:
            words = text_line.split()
            if not words:
                continue
            char_w = 16
            line_w = sum(len(w) * char_w + 12 for w in words)
            start_x = max(20, (img_w - line_w) // 2)

            curr_x = start_x
            for w in words:
                token_w = len(w) * char_w
                tok = TokenBuilder.create_token(
                    text=w,
                    confidence=conf,
                    pixel_x=curr_x,
                    pixel_y=y_pos,
                    pixel_w=token_w,
                    pixel_h=30,
                    img_width=img_w,
                    img_height=img_h,
                )
                tokens.append(tok)
                curr_x += token_w + 12

        return tokens
