import re
from typing import List, Optional

from dateutil import parser as date_parser

from app.modules.ocr.field_extractors.base_extractor import (
    BaseFieldExtractor,
    ExtractedField,
)
from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.pipeline import OCRToken


class DateExtractor(BaseFieldExtractor):
    """Extracts and standardizes certificate issue, convocation, or examination dates."""

    DATE_LABELS = [
        "date of issue",
        "issue date",
        "issued on",
        "dated",
        "date",
        "given under",
        "convocation date",
        "conferred on",
        "passing year",
        "admitted on",
        "day of",
    ]

    DATE_PATTERNS = [
        # 15th June, 2024 or 15 June 2024
        re.compile(
            r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?),?\s+(\d{4})\b",
            re.IGNORECASE,
        ),
        # June 15, 2024
        re.compile(
            r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b",
            re.IGNORECASE,
        ),
        # DD/MM/YYYY or DD-MM-YYYY
        re.compile(r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\b"),
        # Month YYYY (e.g. June 2024)
        re.compile(
            r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})\b",
            re.IGNORECASE,
        ),
    ]

    @property
    def field_name(self) -> str:
        return "issue_date"

    def extract(
        self,
        lines: List[TextLine],
        all_tokens: List[OCRToken],
    ) -> Optional[ExtractedField]:
        """Extract and normalize certificate date to ISO YYYY-MM-DD."""
        if not lines:
            return None

        # Strategy 1: Check lines with date context labels
        for line in lines:
            for label in self.DATE_LABELS:
                if label in line.text.lower():
                    for pattern in self.DATE_PATTERNS:
                        match = pattern.search(line.text)
                        if match:
                            date_str = match.group(0)
                            iso_date = self._normalize_to_iso(date_str)
                            if iso_date:
                                tokens = self._find_matching_tokens(line, date_str)
                                norm_bbox, pix_bbox = self.compute_union_bboxes(tokens)
                                return ExtractedField(
                                    field_name=self.field_name,
                                    value=iso_date,
                                    raw_text=date_str,
                                    confidence=self.calculate_field_confidence(tokens),
                                    bounding_box=norm_bbox,
                                    pixel_bounding_box=pix_bbox,
                                    source_tokens=tokens,
                                )

        # Strategy 2: Scan for any valid date pattern (prioritizing bottom half)
        sorted_candidates = sorted(lines, key=lambda item: item.bbox.y1, reverse=True)
        for line in sorted_candidates:
            for pattern in self.DATE_PATTERNS:
                match = pattern.search(line.text)
                if match:
                    date_str = match.group(0)
                    iso_date = self._normalize_to_iso(date_str)
                    if iso_date:
                        tokens = self._find_matching_tokens(line, date_str)
                        norm_bbox, pix_bbox = self.compute_union_bboxes(tokens)
                        return ExtractedField(
                            field_name=self.field_name,
                            value=iso_date,
                            raw_text=date_str,
                            confidence=self.calculate_field_confidence(tokens),
                            bounding_box=norm_bbox,
                            pixel_bounding_box=pix_bbox,
                            source_tokens=tokens,
                        )

        return None

    def _normalize_to_iso(self, date_str: str) -> Optional[str]:
        try:
            # Clean ordinal suffixes like 15th -> 15
            cleaned = re.sub(r"(\d{1,2})(?:st|nd|rd|th)", r"\1", date_str, flags=re.IGNORECASE)
            parsed = date_parser.parse(cleaned, fuzzy=True, dayfirst=True)
            return parsed.strftime("%Y-%m-%d")
        except Exception:
            return None

    def _find_matching_tokens(self, line: TextLine, target_str: str) -> List[OCRToken]:
        words = set(target_str.lower().split())
        matched = [t for t in line.tokens if any(w in t.text.lower() for w in words)]
        return matched if matched else line.tokens
