import re
from typing import List, Optional

from rapidfuzz import fuzz

from app.modules.ocr.field_extractors.base_extractor import (
    BaseFieldExtractor,
    ExtractedField,
)
from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.pipeline import OCRToken


class DegreeExtractor(BaseFieldExtractor):
    """Extracts degree qualification, program title, and specialization branch."""

    KNOWN_DEGREES = [
        "Bachelor of Technology",
        "Bachelor of Engineering",
        "Bachelor of Science",
        "Bachelor of Arts",
        "Bachelor of Commerce",
        "Bachelor of Computer Applications",
        "Master of Technology",
        "Master of Science",
        "Master of Computer Applications",
        "Master of Business Administration",
        "Doctor of Philosophy",
        "B.Tech",
        "B.E.",
        "B.Sc",
        "M.Tech",
        "Ph.D.",
        "MBA",
        "Diploma in Engineering",
    ]

    DISCIPLINES = [
        "Computer Science and Engineering",
        "Information Science and Engineering",
        "Electronics and Communication Engineering",
        "Electrical and Electronics Engineering",
        "Mechanical Engineering",
        "Civil Engineering",
        "Artificial Intelligence and Machine Learning",
        "Data Science",
        "Cyber Security",
        "Biotechnology",
        "Business Administration",
    ]

    @property
    def field_name(self) -> str:
        return "course_degree"

    def extract(
        self,
        lines: List[TextLine],
        all_tokens: List[OCRToken],
    ) -> Optional[ExtractedField]:
        """Extract degree and program from lines."""
        if not lines:
            return None

        # Strategy 1: Search for degree indicator phrases
        phrase_field = self._search_degree_phrases(lines)
        if phrase_field:
            return phrase_field

        # Strategy 2: Fuzzy match known degree titles
        return self._fuzzy_search_degrees(lines)

    def _search_degree_phrases(self, lines: List[TextLine]) -> Optional[ExtractedField]:
        pattern = re.compile(
            r"(?:degree of|admitted to the degree of|conferred the degree of|"
            r"completed the course of)\s+([A-Za-z\s\.\,\(\)\-]+)",
            re.IGNORECASE,
        )
        for i, line in enumerate(lines):
            match = pattern.search(line.text)
            if match:
                deg_str = match.group(1).strip()
                # Check if next line contains specialization continuation
                combined_tokens = list(line.tokens)
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if re.search(
                        r"^(?:in|branch of|specialization in)\b", next_line.text, re.IGNORECASE
                    ):
                        deg_str += " " + next_line.text.strip()
                        combined_tokens.extend(next_line.tokens)

                cleaned = self._clean_degree(deg_str)
                if len(cleaned) >= 4:
                    norm_bbox, pix_bbox = self.compute_union_bboxes(combined_tokens)
                    return ExtractedField(
                        field_name=self.field_name,
                        value=cleaned,
                        raw_text=deg_str,
                        confidence=self.calculate_field_confidence(combined_tokens),
                        bounding_box=norm_bbox,
                        pixel_bounding_box=pix_bbox,
                        source_tokens=combined_tokens,
                    )
        return None

    def _fuzzy_search_degrees(self, lines: List[TextLine]) -> Optional[ExtractedField]:
        best_line: Optional[TextLine] = None
        best_score = 0.0

        for line in lines:
            line_text = line.text
            for deg in self.KNOWN_DEGREES:
                score = fuzz.partial_ratio(deg.lower(), line_text.lower())
                if score >= 80 and score > best_score:
                    best_score = score
                    best_line = line

        if best_line is not None:
            val = self._clean_degree(best_line.text)
            norm_bbox, pix_bbox = self.compute_union_bboxes(best_line.tokens)
            return ExtractedField(
                field_name=self.field_name,
                value=val,
                raw_text=best_line.text,
                confidence=self.calculate_field_confidence(best_line.tokens),
                bounding_box=norm_bbox,
                pixel_bounding_box=pix_bbox,
                source_tokens=best_line.tokens,
            )
        return None

    def _clean_degree(self, text: str) -> str:
        # Strip phrases like "has been admitted to" if accidentally captured
        pattern = (
            r"^(?:the\s+degree\s+of|admitted\s+to\s+the\s+degree\s+of|"
            r"has\s+been\s+conferred\s+the\s+degree\s+of)\s*"
        )
        cleaned = re.sub(pattern, "", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"[\t\r\n]+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" :;,-_")
        return cleaned
