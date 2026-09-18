import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from rapidfuzz import fuzz

from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.pipeline import OCRToken
from app.schemas.primitives import BoundingBox, PixelBoundingBox


@dataclass
class ExtractedField:
    """Represents a successfully extracted academic certificate field with
    spatial and confidence metadata.
    """

    field_name: str
    value: str
    raw_text: str
    confidence: float
    bounding_box: BoundingBox
    pixel_bounding_box: PixelBoundingBox
    source_tokens: List[OCRToken] = field(default_factory=list)
    is_flagged: bool = False


class BaseFieldExtractor(ABC):
    """Abstract base class for all entity field extractors."""

    @property
    @abstractmethod
    def field_name(self) -> str:
        """Name of the target field (e.g. 'student_name', 'register_number')."""
        pass

    @abstractmethod
    def extract(
        self,
        lines: List[TextLine],
        all_tokens: List[OCRToken],
    ) -> Optional[ExtractedField]:
        """Extract field value, confidence, and bounding box from lines and tokens."""
        pass

    @staticmethod
    def fuzzy_match_label(
        line_text: str,
        target_labels: Sequence[str],
        threshold: float = 75.0,
    ) -> Optional[Tuple[str, float]]:
        """Check if any label pattern approximately appears in the line text using RapidFuzz."""
        norm_line = line_text.lower().strip()
        best_label: Optional[str] = None
        best_score = 0.0

        for label in target_labels:
            label_norm = label.lower().strip()
            score = fuzz.partial_ratio(label_norm, norm_line)
            if score >= threshold and score > best_score:
                best_score = score
                best_label = label

        if best_label is not None:
            return best_label, best_score
        return None

    @staticmethod
    def calculate_field_confidence(tokens: List[OCRToken]) -> float:
        """Compute character-length-weighted mean confidence across constituent tokens."""
        if not tokens:
            return 0.0
        total_chars = sum(len(t.text) for t in tokens)
        if total_chars == 0:
            return sum(t.confidence for t in tokens) / len(tokens)
        weighted_sum = sum(t.confidence * len(t.text) for t in tokens)
        return max(0.0, min(1.0, weighted_sum / total_chars))

    @staticmethod
    def compute_union_bboxes(
        tokens: List[OCRToken],
    ) -> Tuple[BoundingBox, PixelBoundingBox]:
        """Compute combined normalized and pixel bounding boxes for a list of tokens."""
        if not tokens:
            return (
                BoundingBox(x1=0.0, y1=0.0, x2=0.0, y2=0.0),
                PixelBoundingBox(x=0, y=0, width=1, height=1),
            )

        min_x = min(t.bbox.x1 for t in tokens)
        min_y = min(t.bbox.y1 for t in tokens)
        max_x = max(t.bbox.x2 for t in tokens)
        max_y = max(t.bbox.y2 for t in tokens)

        pix_x = min(t.pixel_bbox.x for t in tokens)
        pix_y = min(t.pixel_bbox.y for t in tokens)
        pix_r = max(t.pixel_bbox.x + t.pixel_bbox.width for t in tokens)
        pix_b = max(t.pixel_bbox.y + t.pixel_bbox.height for t in tokens)

        norm_box = BoundingBox(x1=min_x, y1=min_y, x2=max_x, y2=max_y)
        pix_box = PixelBoundingBox(
            x=pix_x,
            y=pix_y,
            width=max(1, pix_r - pix_x),
            height=max(1, pix_b - pix_y),
        )
        return norm_box, pix_box

    @staticmethod
    def clean_text(text: str) -> str:
        """Strip surrounding punctuation, multiple spaces, and non-printable noise."""
        cleaned = re.sub(r"[\t\r\n]+", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip(" :;,-_")
