import re
from typing import List, Optional

from app.modules.ocr.field_extractors.base_extractor import (
    BaseFieldExtractor,
    ExtractedField,
)
from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.pipeline import OCRToken


class GradeExtractor(BaseFieldExtractor):
    """Extracts CGPA, GPA, percentage, and graduation division/class."""

    CGPA_PATTERN = re.compile(
        r"\b(?:cgpa|gpa|grade|marks|academic performance)?\s*[:\-]?"
        r"\s*([0-9]\.[0-9]{1,2}(?:\s*\/\s*(?:10(?:\.0)?|4(?:\.0)?))?)\b",
        re.IGNORECASE,
    )
    PERCENT_PATTERN = re.compile(r"\b([0-9]{2}(?:\.[0-9]{1,2})?)\s*%\b")
    DIVISION_PATTERN = re.compile(
        r"\b(first class with distinction|first class|second class|"
        r"pass class|distinction|exemplary|honours)\b",
        re.IGNORECASE,
    )

    @property
    def field_name(self) -> str:
        return "grade_or_marks"

    def extract(
        self,
        lines: List[TextLine],
        all_tokens: List[OCRToken],
    ) -> Optional[ExtractedField]:
        """Extract grade, CGPA, or class division from text lines."""
        if not lines:
            return None

        for line in lines:
            text = line.text
            found_parts = []
            matched_tokens = []

            # Check CGPA
            cgpa_match = self.CGPA_PATTERN.search(text)
            if cgpa_match:
                val = cgpa_match.group(1).strip()
                # Validate numeric sanity
                try:
                    num = float(val.split("/")[0].strip())
                    if 0.0 <= num <= 10.0:
                        found_parts.append(f"CGPA: {val}")
                        matched_tokens.extend(
                            [t for t in line.tokens if any(c.isdigit() for c in t.text)]
                        )
                except ValueError:
                    pass

            # Check Percentage
            pct_match = self.PERCENT_PATTERN.search(text)
            if pct_match:
                val = pct_match.group(1).strip()
                try:
                    pct = float(val)
                    if 30.0 <= pct <= 100.0:
                        found_parts.append(f"{val}%")
                except ValueError:
                    pass

            # Check Division
            div_match = self.DIVISION_PATTERN.search(text)
            if div_match:
                div_str = div_match.group(1).title()
                found_parts.append(div_str)
                matched_tokens.extend([t for t in line.tokens if t.text.lower() in div_str.lower()])

            if found_parts:
                combined_value = " - ".join(found_parts)
                tokens = matched_tokens if matched_tokens else line.tokens
                norm_bbox, pix_bbox = self.compute_union_bboxes(tokens)
                return ExtractedField(
                    field_name=self.field_name,
                    value=combined_value,
                    raw_text=text,
                    confidence=self.calculate_field_confidence(tokens),
                    bounding_box=norm_bbox,
                    pixel_bounding_box=pix_bbox,
                    source_tokens=tokens,
                )

        return None
