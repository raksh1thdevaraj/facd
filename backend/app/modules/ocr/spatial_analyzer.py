from dataclasses import dataclass, field
from typing import List, Optional

from app.schemas.pipeline import OCRToken
from app.schemas.primitives import BoundingBox, PixelBoundingBox


@dataclass
class TextLine:
    """Represents a coherent horizontal line of text reconstructed from OCR tokens."""

    tokens: List[OCRToken] = field(default_factory=list)
    text: str = ""
    bbox: BoundingBox = field(default_factory=lambda: BoundingBox(x1=0.0, y1=0.0, x2=0.0, y2=0.0))
    pixel_bbox: PixelBoundingBox = field(
        default_factory=lambda: PixelBoundingBox(x=0, y=0, width=1, height=1)
    )
    mean_confidence: float = 0.0
    y_center: float = 0.0

    @classmethod
    def from_tokens(cls, tokens: List[OCRToken]) -> "TextLine":
        """Construct a TextLine from a list of horizontally sorted tokens."""
        if not tokens:
            return cls()

        sorted_tokens = sorted(tokens, key=lambda t: t.pixel_bbox.x)
        text = " ".join(t.text for t in sorted_tokens).strip()

        # Compute union of bounding boxes
        min_x = min(t.bbox.x1 for t in sorted_tokens)
        min_y = min(t.bbox.y1 for t in sorted_tokens)
        max_x = max(t.bbox.x2 for t in sorted_tokens)
        max_y = max(t.bbox.y2 for t in sorted_tokens)
        union_bbox = BoundingBox(
            x1=min_x,
            y1=min_y,
            x2=max_x,
            y2=max_y,
        )

        # Union of pixel boxes
        pix_x = min(t.pixel_bbox.x for t in sorted_tokens)
        pix_y = min(t.pixel_bbox.y for t in sorted_tokens)
        pix_r = max(t.pixel_bbox.x + t.pixel_bbox.width for t in sorted_tokens)
        pix_b = max(t.pixel_bbox.y + t.pixel_bbox.height for t in sorted_tokens)
        union_pixel_bbox = PixelBoundingBox(
            x=pix_x,
            y=pix_y,
            width=max(1, pix_r - pix_x),
            height=max(1, pix_b - pix_y),
        )

        mean_conf = sum(t.confidence for t in sorted_tokens) / len(sorted_tokens)
        y_center = pix_y + (pix_b - pix_y) / 2.0

        return cls(
            tokens=sorted_tokens,
            text=text,
            bbox=union_bbox,
            pixel_bbox=union_pixel_bbox,
            mean_confidence=mean_conf,
            y_center=y_center,
        )


class SpatialLayoutAnalyzer:
    """Analyzes 2D spatial layout of OCR tokens, segmenting them into lines and reading order."""

    @staticmethod
    def group_tokens_into_lines(
        tokens: List[OCRToken],
        overlap_threshold: float = 0.45,
    ) -> List[TextLine]:
        """Group detected OCR tokens into horizontal text lines and sort in reading order."""
        if not tokens:
            return []

        # Sort tokens by vertical center
        sorted_by_y = sorted(
            tokens,
            key=lambda t: t.pixel_bbox.y + (t.pixel_bbox.height / 2.0),
        )

        lines: List[List[OCRToken]] = []

        for token in sorted_by_y:
            t_top = token.pixel_bbox.y
            t_bot = token.pixel_bbox.y + token.pixel_bbox.height
            t_h = max(1, token.pixel_bbox.height)
            t_center = t_top + t_h / 2.0

            best_line_idx: Optional[int] = None
            best_overlap = 0.0

            for idx, current_line in enumerate(lines):
                line_top = min(tok.pixel_bbox.y for tok in current_line)
                line_bot = max(tok.pixel_bbox.y + tok.pixel_bbox.height for tok in current_line)
                line_h = max(1, line_bot - line_top)

                # Overlap between token and line
                overlap_top = max(t_top, line_top)
                overlap_bot = min(t_bot, line_bot)
                overlap_h = max(0, overlap_bot - overlap_top)

                min_h = min(t_h, line_h)
                overlap_ratio = overlap_h / min_h if min_h > 0 else 0.0

                # Also check vertical center proximity
                line_center = line_top + line_h / 2.0
                center_dist = abs(t_center - line_center)

                if overlap_ratio >= overlap_threshold or center_dist <= (line_h * 0.4):
                    if overlap_ratio > best_overlap:
                        best_overlap = overlap_ratio
                        best_line_idx = idx

            if best_line_idx is not None:
                lines[best_line_idx].append(token)
            else:
                lines.append([token])

        # Convert to TextLine objects and sort top-to-bottom
        text_lines = [TextLine.from_tokens(line_tokens) for line_tokens in lines if line_tokens]
        text_lines.sort(key=lambda line: line.pixel_bbox.y)
        return text_lines

    @staticmethod
    def find_tokens_to_right(
        anchor_token: OCRToken,
        line: TextLine,
        max_gap_px: Optional[int] = None,
    ) -> List[OCRToken]:
        """Find tokens strictly to the right of an anchor token on the same line."""
        anchor_right = anchor_token.pixel_bbox.x + anchor_token.pixel_bbox.width
        right_tokens: List[OCRToken] = []

        for tok in line.tokens:
            if tok.pixel_bbox.x >= anchor_right - 2:  # allow 2px tolerance
                if max_gap_px is not None:
                    gap = tok.pixel_bbox.x - anchor_right
                    if gap > max_gap_px:
                        break
                right_tokens.append(tok)

        return right_tokens

    @staticmethod
    def find_line_below(
        anchor_line: TextLine,
        all_lines: List[TextLine],
        max_vertical_gap_px: int = 150,
    ) -> Optional[TextLine]:
        """Find the immediate next text line below the anchor line within a vertical distance."""
        anchor_bottom = anchor_line.pixel_bbox.y + anchor_line.pixel_bbox.height
        candidates = [
            line
            for line in all_lines
            if line.pixel_bbox.y >= anchor_bottom - 5
            and (line.pixel_bbox.y - anchor_bottom) <= max_vertical_gap_px
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda item: item.pixel_bbox.y)
        return candidates[0]

    @staticmethod
    def filter_by_vertical_band(
        lines: List[TextLine],
        min_rel_y: float = 0.0,
        max_rel_y: float = 1.0,
    ) -> List[TextLine]:
        """Filter lines whose vertical position falls within a normalized
        vertical band [min, max].
        """
        return [line for line in lines if line.bbox.y1 >= min_rel_y and line.bbox.y2 <= max_rel_y]
