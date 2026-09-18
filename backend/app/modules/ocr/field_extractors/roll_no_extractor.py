import re
from typing import List, Optional

from app.modules.ocr.field_extractors.base_extractor import (
    BaseFieldExtractor,
    ExtractedField,
)
from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.pipeline import OCRToken


class RollNumberExtractor(BaseFieldExtractor):
    """Extracts student roll number, registration number, USN, or enrollment ID."""

    ROLL_LABELS = [
        "usn",
        "roll no",
        "roll number",
        "reg no",
        "reg. no",
        "registration no",
        "registration number",
        "enrollment no",
        "enrollment number",
        "prn",
        "hall ticket no",
        "student id",
        "id no",
    ]

    # Specific format regexes
    USN_PATTERN = re.compile(r"\b([1-4][A-Z]{2}\d{2}[A-Z]{2}\d{3})\b", re.IGNORECASE)
    ALPHANUM_ID_PATTERN = re.compile(r"\b([A-Z0-9]{6,16})\b", re.IGNORECASE)
    NUMERIC_ID_PATTERN = re.compile(r"\b(\d{6,14})\b")

    @property
    def field_name(self) -> str:
        return "register_number"

    def extract(
        self,
        lines: List[TextLine],
        all_tokens: List[OCRToken],
    ) -> Optional[ExtractedField]:
        """Extract registration / roll number via labels and strict pattern matches."""
        if not lines:
            return None

        # Strategy 1: Check for USN pattern directly (very high specificity)
        usn_field = self._search_usn_pattern(lines)
        if usn_field:
            return usn_field

        # Strategy 2: Label-based extraction
        label_field = self._search_by_label(lines)
        if label_field:
            return label_field

        return None

    def _search_usn_pattern(self, lines: List[TextLine]) -> Optional[ExtractedField]:
        for line in lines:
            match = self.USN_PATTERN.search(line.text)
            if match:
                val = match.group(1).upper()
                matched_tokens = [t for t in line.tokens if val in t.text.upper()]
                tokens = matched_tokens if matched_tokens else line.tokens
                norm_bbox, pix_bbox = self.compute_union_bboxes(tokens)
                return ExtractedField(
                    field_name=self.field_name,
                    value=val,
                    raw_text=match.group(0),
                    confidence=self.calculate_field_confidence(tokens),
                    bounding_box=norm_bbox,
                    pixel_bounding_box=pix_bbox,
                    source_tokens=tokens,
                )
        return None

    def _search_by_label(self, lines: List[TextLine]) -> Optional[ExtractedField]:
        for i, line in enumerate(lines):
            for label in self.ROLL_LABELS:
                pattern = rf"\b{re.escape(label)}\b\s*[:\-]?\s*(.+)"
                match = re.search(pattern, line.text, re.IGNORECASE)
                if match:
                    trailing = match.group(1).strip()
                    cand = self._extract_id_from_string(trailing)
                    if cand:
                        matched_tokens = [t for t in line.tokens if cand.lower() in t.text.lower()]
                        tokens = matched_tokens if matched_tokens else line.tokens
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

                    # If label was alone, check line directly below
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        cand = self._extract_id_from_string(next_line.text)
                        if cand:
                            cand_low = cand.lower()
                            matched_tokens = [
                                t for t in next_line.tokens if cand_low in t.text.lower()
                            ]
                            tokens = matched_tokens if matched_tokens else next_line.tokens
                            norm_bbox, pix_bbox = self.compute_union_bboxes(tokens)
                            return ExtractedField(
                                field_name=self.field_name,
                                value=cand,
                                raw_text=next_line.text,
                                confidence=self.calculate_field_confidence(tokens),
                                bounding_box=norm_bbox,
                                pixel_bounding_box=pix_bbox,
                                source_tokens=tokens,
                            )
        return None

    def _extract_id_from_string(self, text: str) -> Optional[str]:
        cleaned = text.strip(" :;,-_")
        words = cleaned.split()
        if not words:
            return None

        # Check first token or full words for ID format
        for w in words:
            w_clean = re.sub(r"[^A-Za-z0-9]", "", w)
            if 5 <= len(w_clean) <= 16:
                # Must have at least some digits or be valid USN/Roll
                if any(c.isdigit() for c in w_clean):
                    return w_clean.upper()
        return None
