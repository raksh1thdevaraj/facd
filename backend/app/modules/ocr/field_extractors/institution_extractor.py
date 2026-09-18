import re
from typing import List, Optional

from app.modules.ocr.field_extractors.base_extractor import (
    BaseFieldExtractor,
    ExtractedField,
)
from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.pipeline import OCRToken


class InstitutionExtractor(BaseFieldExtractor):
    """Extracts issuing university or college name from the header region of the certificate."""

    INSTITUTION_KEYWORDS = [
        "university",
        "institute of technology",
        "national institute",
        "indian institute",
        "college of engineering",
        "vidyapeeth",
        "deemed university",
        "academy of higher education",
        "polytechnic",
        "board of technical education",
        "autonomous college",
    ]

    @property
    def field_name(self) -> str:
        return "institution_name"

    def extract(
        self,
        lines: List[TextLine],
        all_tokens: List[OCRToken],
    ) -> Optional[ExtractedField]:
        """Extract institution name from header lines (top 40% of document)."""
        if not lines:
            return None

        # Filter lines in top 40% of certificate
        header_lines = [line for line in lines if line.bbox.y1 <= 0.40]
        if not header_lines:
            header_lines = lines[:3]

        best_line: Optional[TextLine] = None
        best_priority = -1

        for line in header_lines:
            text_lower = line.text.lower()
            for priority, kw in enumerate(self.INSTITUTION_KEYWORDS):
                if kw in text_lower:
                    # Higher priority if specific
                    if priority > best_priority or best_line is None:
                        best_priority = priority
                        best_line = line
                    break

        if best_line is not None:
            val = self._clean_institution(best_line.text)
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

        # Fallback: Topmost uppercase line if at least 3 words
        for line in header_lines[:2]:
            words = line.text.split()
            if len(words) >= 3 and all(w.isupper() or w.istitle() for w in words):
                val = self._clean_institution(line.text)
                norm_bbox, pix_bbox = self.compute_union_bboxes(line.tokens)
                return ExtractedField(
                    field_name=self.field_name,
                    value=val,
                    raw_text=line.text,
                    confidence=self.calculate_field_confidence(line.tokens),
                    bounding_box=norm_bbox,
                    pixel_bounding_box=pix_bbox,
                    source_tokens=line.tokens,
                )

        return None

    def _clean_institution(self, text: str) -> str:
        cleaned = re.sub(r"[\t\r\n]+", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" :;,-_")
        return cleaned
