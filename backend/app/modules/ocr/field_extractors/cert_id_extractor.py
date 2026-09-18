import re
from typing import List, Optional

import cv2
import numpy as np

from app.modules.ocr.field_extractors.base_extractor import (
    BaseFieldExtractor,
    ExtractedField,
)
from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.pipeline import OCRToken
from app.schemas.primitives import BoundingBox, PixelBoundingBox


class CertificateIdExtractor(BaseFieldExtractor):
    """Extracts unique printed certificate serial numbers, folio numbers, and QR code payloads."""

    SERIAL_LABELS = [
        "certificate no",
        "certificate number",
        "sl no",
        "sl. no",
        "serial no",
        "serial number",
        "folio no",
        "folio number",
        "cert no",
        "cert. no",
        "sr no",
        "sr. no",
    ]

    SERIAL_PATTERN = re.compile(
        r"\b([A-Z]{2,6}[-\/]\d{2,4}[-\/][A-Z0-9]{4,12})\b",
        re.IGNORECASE,
    )
    ALPHANUM_SERIAL = re.compile(r"\b([A-Z0-9]{6,16})\b", re.IGNORECASE)

    @property
    def field_name(self) -> str:
        return "certificate_number"

    def extract(
        self,
        lines: List[TextLine],
        all_tokens: List[OCRToken],
        image: Optional[np.ndarray] = None,
    ) -> Optional[ExtractedField]:
        """Extract certificate ID through QR code detection or printed serial label heuristics."""
        # Check for QR code on the canvas first
        if image is not None:
            qr_field = self._detect_qr_code(image)
            if qr_field:
                return qr_field

        if not lines:
            return None

        # Check explicit labels
        for line in lines:
            for label in self.SERIAL_LABELS:
                pattern = rf"\b{re.escape(label)}\b\s*[:\-]?\s*(.+)"
                match = re.search(pattern, line.text, re.IGNORECASE)
                if match:
                    trailing = match.group(1).strip()
                    cand = self._parse_serial(trailing)
                    if cand:
                        tokens = [t for t in line.tokens if cand.lower() in t.text.lower()]
                        tokens = tokens if tokens else line.tokens
                        norm_bbox, pix_bbox = self.compute_union_bboxes(tokens)
                        return ExtractedField(
                            field_name=self.field_name,
                            value=cand,
                            raw_text=trailing,
                            confidence=self.calculate_field_confidence(tokens),
                            bounding_box=norm_bbox,
                            pixel_bounding_box=pix_bbox,
                            source_tokens=tokens,
                        )

        # Check pattern match like VTU-2024-889921 anywhere in document
        for line in lines:
            match = self.SERIAL_PATTERN.search(line.text)
            if match:
                cand = match.group(1).upper()
                tokens = [t for t in line.tokens if cand in t.text.upper()]
                tokens = tokens if tokens else line.tokens
                norm_bbox, pix_bbox = self.compute_union_bboxes(tokens)
                return ExtractedField(
                    field_name=self.field_name,
                    value=cand,
                    raw_text=match.group(0),
                    confidence=self.calculate_field_confidence(tokens),
                    bounding_box=norm_bbox,
                    pixel_bounding_box=pix_bbox,
                    source_tokens=tokens,
                )

        return None

    def _parse_serial(self, text: str) -> Optional[str]:
        words = text.strip(" :;,-_").split()
        if not words:
            return None
        # Check structured pattern first
        for w in words:
            if self.SERIAL_PATTERN.match(w):
                return w.upper()
        # Check general alphanumeric string with digits
        for w in words:
            w_clean = re.sub(r"[^A-Za-z0-9\-_]", "", w)
            if 5 <= len(w_clean) <= 20 and any(c.isdigit() for c in w_clean):
                return w_clean.upper()
        return None

    def _detect_qr_code(self, image: np.ndarray) -> Optional[ExtractedField]:
        """Detect and decode QR code using OpenCV QRCodeDetector."""
        try:
            detector = cv2.QRCodeDetector()
            val, points, _ = detector.detectAndDecode(image)
            if val and points is not None and len(points) > 0:
                pts = points[0]
                img_h, img_w = image.shape[:2]
                xs = [p[0] for p in pts]
                ys = [p[1] for p in pts]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)

                norm_bbox = BoundingBox(
                    x1=max(0.0, min_x / img_w),
                    y1=max(0.0, min_y / img_h),
                    x2=min(1.0, max_x / img_w),
                    y2=min(1.0, max_y / img_h),
                )
                pix_bbox = PixelBoundingBox(
                    x=int(min_x),
                    y=int(min_y),
                    width=max(1, int(max_x - min_x)),
                    height=max(1, int(max_y - min_y)),
                )
                return ExtractedField(
                    field_name=self.field_name,
                    value=val.strip(),
                    raw_text=f"QR: {val.strip()}",
                    confidence=1.0,
                    bounding_box=norm_bbox,
                    pixel_bounding_box=pix_bbox,
                    source_tokens=[],
                )
        except Exception:
            pass
        return None
