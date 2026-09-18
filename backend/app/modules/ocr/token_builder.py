from dataclasses import dataclass
from typing import Any, Dict, List, NamedTuple, Sequence, Tuple

from app.schemas.pipeline import OCRToken
from app.schemas.primitives import BoundingBox, PixelBoundingBox


class Point(NamedTuple):
    """2D coordinate point."""

    x: float
    y: float


@dataclass
class GeometricBoundingBox:
    """Rich geometric bounding box with polygon, bounds, and spatial query methods."""

    polygon: List[Point]
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    width: float
    height: float
    center: Point

    @classmethod
    def from_polygon(cls, polygon: Sequence[Sequence[float]]) -> "GeometricBoundingBox":
        """Construct a GeometricBoundingBox from a 4-point polygon [(x, y), ...]."""
        pts = [Point(float(p[0]), float(p[1])) for p in polygon]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        x_min = min(xs)
        x_max = max(xs)
        y_min = min(ys)
        y_max = max(ys)
        w = max(0.0, x_max - x_min)
        h = max(0.0, y_max - y_min)
        center = Point(x_min + w / 2.0, y_min + h / 2.0)
        return cls(
            polygon=pts,
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max,
            width=w,
            height=h,
            center=center,
        )

    def to_relative_bbox(
        self, img_width: int, img_height: int
    ) -> Tuple[BoundingBox, PixelBoundingBox]:
        """Convert to canonical normalized BoundingBox [0.0, 1.0] and PixelBoundingBox."""
        safe_w = max(1, img_width)
        safe_h = max(1, img_height)

        rel_x_min = max(0.0, min(1.0, self.x_min / safe_w))
        rel_y_min = max(0.0, min(1.0, self.y_min / safe_h))
        rel_x_max = max(rel_x_min, min(1.0, self.x_max / safe_w))
        rel_y_max = max(rel_y_min, min(1.0, self.y_max / safe_h))

        norm_bbox = BoundingBox(
            x1=rel_x_min,
            y1=rel_y_min,
            x2=rel_x_max,
            y2=rel_y_max,
        )
        pix_bbox = PixelBoundingBox(
            x=max(0, int(round(self.x_min))),
            y=max(0, int(round(self.y_min))),
            width=max(1, int(round(self.width))),
            height=max(1, int(round(self.height))),
        )
        return norm_bbox, pix_bbox

    def horizontal_distance_to(self, other: "GeometricBoundingBox") -> float:
        """Calculate signed horizontal distance from this box's right edge to other's left edge."""
        return other.x_min - self.x_max

    def vertical_overlap_ratio(self, other: "GeometricBoundingBox") -> float:
        """Calculate vertical overlap ratio relative to the smaller box's height."""
        overlap_y_min = max(self.y_min, other.y_min)
        overlap_y_max = min(self.y_max, other.y_max)
        overlap_h = max(0.0, overlap_y_max - overlap_y_min)
        min_h = min(self.height, other.height)
        if min_h <= 0.0:
            return 0.0
        return overlap_h / min_h


class TokenBuilder:
    """Constructs canonical OCRToken objects from raw OCR engine outputs."""

    @staticmethod
    def from_easyocr_result(
        raw_result: Sequence[Any],
        img_width: int,
        img_height: int,
    ) -> List[OCRToken]:
        """Build OCRTokens from EasyOCR detection tuples: (polygon, text, confidence)."""
        tokens: List[OCRToken] = []
        for item in raw_result:
            if len(item) < 3:
                continue
            polygon, text, conf = item[0], item[1], item[2]
            cleaned_text = str(text).strip()
            if not cleaned_text:
                continue

            geo_bbox = GeometricBoundingBox.from_polygon(polygon)
            norm_bbox, pix_bbox = geo_bbox.to_relative_bbox(img_width, img_height)
            confidence = max(0.0, min(1.0, float(conf)))

            tokens.append(
                OCRToken(
                    text=cleaned_text,
                    confidence=confidence,
                    bbox=norm_bbox,
                    pixel_bbox=pix_bbox,
                )
            )
        return tokens

    @staticmethod
    def from_tesseract_data(
        data: Dict[str, List[Any]],
        img_width: int,
        img_height: int,
    ) -> List[OCRToken]:
        """Build OCRTokens from pytesseract image_to_data dict."""
        tokens: List[OCRToken] = []
        n_boxes = len(data.get("text", []))
        for i in range(n_boxes):
            text = str(data["text"][i]).strip()
            if not text:
                continue

            conf_raw = float(data["conf"][i])
            if conf_raw < 0:  # Tesseract uses -1 for block/par/line headers
                continue
            confidence = max(0.0, min(1.0, conf_raw / 100.0))

            x = float(data["left"][i])
            y = float(data["top"][i])
            w = float(data["width"][i])
            h = float(data["height"][i])

            polygon = [
                [x, y],
                [x + w, y],
                [x + w, y + h],
                [x, y + h],
            ]
            geo_bbox = GeometricBoundingBox.from_polygon(polygon)
            norm_bbox, pix_bbox = geo_bbox.to_relative_bbox(img_width, img_height)

            tokens.append(
                OCRToken(
                    text=text,
                    confidence=confidence,
                    bbox=norm_bbox,
                    pixel_bbox=pix_bbox,
                )
            )
        return tokens

    @staticmethod
    def create_token(
        text: str,
        confidence: float,
        pixel_x: int,
        pixel_y: int,
        pixel_w: int,
        pixel_h: int,
        img_width: int,
        img_height: int,
    ) -> OCRToken:
        """Utility factory to create a single OCRToken with exact geometry."""
        polygon = [
            [pixel_x, pixel_y],
            [pixel_x + pixel_w, pixel_y],
            [pixel_x + pixel_w, pixel_y + pixel_h],
            [pixel_x, pixel_y + pixel_h],
        ]
        geo_bbox = GeometricBoundingBox.from_polygon(polygon)
        norm_bbox, pix_bbox = geo_bbox.to_relative_bbox(img_width, img_height)
        return OCRToken(
            text=text.strip(),
            confidence=max(0.0, min(1.0, confidence)),
            bbox=norm_bbox,
            pixel_bbox=pix_bbox,
        )
