import re
from typing import List, Optional

from app.modules.ocr.field_extractors.base_extractor import (
    BaseFieldExtractor,
    ExtractedField,
)
from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.pipeline import OCRToken


class StudentNameExtractor(BaseFieldExtractor):
    """Extracts student/candidate name from certificate layout."""

    NAME_LABELS = [
        "student name",
        "name of student",
        "name of the student",
        "candidate name",
        "name of candidate",
        "name of the candidate",
        "candidate's name",
        "name",
    ]

    PREFIX_PATTERNS = [
        re.compile(
            r"(?:this is to certify that|certifies that|certify that|presented to|"
            r"conferred upon|awarded to)\s+([A-Za-z\s\.\,\'\-]+?)"
            r"(?:\s+(?:having|son of|daughter of|bearing|who has|of the|"
            r"has been|for successfully|in recognition|\,|$))",
            re.IGNORECASE,
        ),
    ]

    DISALLOWED_WORDS = {
        "university",
        "institute",
        "college",
        "board",
        "technology",
        "sciences",
        "engineering",
        "bachelor",
        "master",
        "doctor",
        "diploma",
        "certificate",
        "department",
        "faculty",
        "governor",
        "chancellor",
        "registrar",
    }

    @property
    def field_name(self) -> str:
        return "student_name"

    def extract(
        self,
        lines: List[TextLine],
        all_tokens: List[OCRToken],
    ) -> Optional[ExtractedField]:
        """Extract student name using labeled key-value, prefix patterns, and uppercase layout."""
        if not lines:
            return None

        # Strategy 1: Explicit label match (e.g., "Name: John Doe")
        field = self._extract_by_label(lines)
        if field:
            return field

        # Strategy 2: Prefix phrases across lines (e.g., "This is to certify that...")
        field = self._extract_by_prefix(lines)
        if field:
            return field

        # Strategy 3: Standalone uppercase prominent line
        return self._extract_by_prominence(lines)

    def _extract_by_label(self, lines: List[TextLine]) -> Optional[ExtractedField]:
        for i, line in enumerate(lines):
            for label in self.NAME_LABELS:
                pattern = rf"\b{re.escape(label)}\b\s*[:\-]?\s*(.+)"
                match = re.search(pattern, line.text, re.IGNORECASE)
                if match:
                    val_str = match.group(1).strip()
                    if val_str:
                        cleaned = self._clean_name(val_str)
                        if self._is_valid_name(cleaned):
                            # Find matching tokens in this line
                            matching_tokens = [
                                t
                                for t in line.tokens
                                if t.text.lower() not in label and t.text.strip(":-") in cleaned
                            ]
                            tokens = matching_tokens if matching_tokens else line.tokens
                            norm_bbox, pix_bbox = self.compute_union_bboxes(tokens)
                            return ExtractedField(
                                field_name=self.field_name,
                                value=cleaned,
                                raw_text=val_str,
                                confidence=self.calculate_field_confidence(tokens),
                                bounding_box=norm_bbox,
                                pixel_bounding_box=pix_bbox,
                                source_tokens=tokens,
                            )
                    # If label was present alone on line, check line below
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        cleaned_next = self._clean_name(next_line.text)
                        if self._is_valid_name(cleaned_next):
                            norm_bbox, pix_bbox = self.compute_union_bboxes(next_line.tokens)
                            return ExtractedField(
                                field_name=self.field_name,
                                value=cleaned_next,
                                raw_text=next_line.text,
                                confidence=self.calculate_field_confidence(next_line.tokens),
                                bounding_box=norm_bbox,
                                pixel_bounding_box=pix_bbox,
                                source_tokens=next_line.tokens,
                            )
        return None

    def _extract_by_prefix(self, lines: List[TextLine]) -> Optional[ExtractedField]:
        full_text = " ".join(line_item.text for line_item in lines)
        for pattern in self.PREFIX_PATTERNS:
            match = pattern.search(full_text)
            if match:
                candidate = match.group(1).strip()
                cleaned = self._clean_name(candidate)
                if self._is_valid_name(cleaned):
                    # Identify constituent tokens
                    name_words = set(cleaned.lower().split())
                    matched_tokens = [
                        tok
                        for line_item in lines
                        for tok in line_item.tokens
                        if tok.text.lower().strip(",.") in name_words
                    ]
                    if matched_tokens:
                        norm_bbox, pix_bbox = self.compute_union_bboxes(matched_tokens)
                        return ExtractedField(
                            field_name=self.field_name,
                            value=cleaned,
                            raw_text=candidate,
                            confidence=self.calculate_field_confidence(matched_tokens),
                            bounding_box=norm_bbox,
                            pixel_bounding_box=pix_bbox,
                            source_tokens=matched_tokens,
                        )

        # Check line immediately following "THIS IS TO CERTIFY THAT"
        for i, line in enumerate(lines):
            if re.search(r"certify\s+that|conferred\s+upon|awarded\s+to", line.text, re.IGNORECASE):
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    cleaned = self._clean_name(next_line.text)
                    if self._is_valid_name(cleaned):
                        norm_bbox, pix_bbox = self.compute_union_bboxes(next_line.tokens)
                        return ExtractedField(
                            field_name=self.field_name,
                            value=cleaned,
                            raw_text=next_line.text,
                            confidence=self.calculate_field_confidence(next_line.tokens),
                            bounding_box=norm_bbox,
                            pixel_bounding_box=pix_bbox,
                            source_tokens=next_line.tokens,
                        )
        return None

    def _extract_by_prominence(self, lines: List[TextLine]) -> Optional[ExtractedField]:
        # Filter lines in vertical range [0.25, 0.55]
        candidate_lines = [line_item for line_item in lines if 0.20 <= line_item.bbox.y1 <= 0.65]
        for line in candidate_lines:
            text = line.text.strip()
            # Standalone line of 2 to 4 capitalized words
            words = text.split()
            if 2 <= len(words) <= 5 and all(w.isupper() or w.istitle() for w in words):
                cleaned = self._clean_name(text)
                if self._is_valid_name(cleaned):
                    norm_bbox, pix_bbox = self.compute_union_bboxes(line.tokens)
                    return ExtractedField(
                        field_name=self.field_name,
                        value=cleaned,
                        raw_text=text,
                        confidence=self.calculate_field_confidence(line.tokens),
                        bounding_box=norm_bbox,
                        pixel_bounding_box=pix_bbox,
                        source_tokens=line.tokens,
                    )
        return None

    def _clean_name(self, raw_name: str) -> str:
        name = re.sub(
            r"\b(mr|ms|mrs|shri|sri|dr|kumar|kumari)\.?\b",
            "",
            raw_name,
            flags=re.IGNORECASE,
        )
        name = re.sub(r"[\t\r\n\(\)]+", " ", name)
        name = re.sub(r"\s+", " ", name).strip(" :;,-_")
        return name

    def _is_valid_name(self, name: str) -> bool:
        if not name or len(name) < 3 or len(name) > 60:
            return False
        # Cannot contain digits
        if any(char.isdigit() for char in name):
            return False
        # Cannot contain disallowed keywords
        name_words = {w.lower() for w in name.split()}
        if any(w in self.DISALLOWED_WORDS for w in name_words):
            return False
        return True
