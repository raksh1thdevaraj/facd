from typing import List, Optional, Tuple

import cv2
import numpy as np

from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.pipeline import OCRToken
from app.schemas.text_consistency import AnomalousRegion, AnomalyType, TextConsistencyConfig


class StrokeWidthAnalyzer:
    """Analyzes character stroke widths using Stroke Width Transform and distance transforms
    to detect bold/light font tampering and weight discrepancies across text lines.
    """

    def __init__(self, config: Optional[TextConsistencyConfig] = None):
        self.config = config or TextConsistencyConfig()

    def analyze(
        self,
        image: Optional[np.ndarray],
        text_lines: List[TextLine],
    ) -> Tuple[float, List[AnomalousRegion]]:
        """Compute stroke width metrics across tokens and flag weight discrepancies.

        Returns:
            Tuple of (stroke_weight_consistency_score [0.0, 1.0], list of anomalous regions).
        """
        if image is None or image.size == 0 or not text_lines:
            return 1.0, []

        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        img_h, img_w = gray.shape[:2]
        anomalies: List[AnomalousRegion] = []
        flagged_token_ids = set()

        for line in text_lines:
            tokens = [t for t in line.tokens if len(t.text.strip()) > 1]
            if len(tokens) < 2:
                continue

            token_strokes: List[Tuple[OCRToken, float]] = []

            for token in tokens:
                sw = self._estimate_token_stroke_width(gray, token, img_w, img_h)
                if sw > 0.5:
                    token_strokes.append((token, sw))

            if len(token_strokes) < 2:
                continue

            strokes = [sw for _, sw in token_strokes]
            median_stroke = float(np.median(strokes))

            if median_stroke <= 0.5:
                continue

            for token, sw in token_strokes:
                ratio = abs(sw - median_stroke) / median_stroke

                if ratio > self.config.stroke_width_ratio_threshold:
                    weight_type = "heavier/bolder" if sw > median_stroke else "lighter/thinner"
                    dev_pct = ratio * 100.0
                    severity = min(1.0, max(0.5, (ratio - 0.35) / 0.65))
                    desc = (
                        f"Token '{token.text}' has {weight_type} stroke width "
                        f"({sw:.1f}px vs line median {median_stroke:.1f}px, dev: {dev_pct:.1f}%)"
                    )

                    token_key = (token.pixel_bbox.x, token.pixel_bbox.y, token.text)
                    if token_key not in flagged_token_ids:
                        flagged_token_ids.add(token_key)
                        anomalies.append(
                            AnomalousRegion(
                                anomaly_type=AnomalyType.STROKE_WEIGHT_DISCREPANCY,
                                severity=round(severity, 3),
                                description=desc,
                                bbox=token.bbox,
                                pixel_bbox=token.pixel_bbox,
                                token_text=token.text,
                            )
                        )

        score = max(0.0, 1.0 - min(1.0, 0.20 * len(anomalies)))
        return round(score, 3), anomalies

    def _estimate_token_stroke_width(
        self, gray_img: np.ndarray, token: OCRToken, img_w: int, img_h: int
    ) -> float:
        """Estimate the mean stroke width of characters within a token's bounding box."""
        # Extract pixel bounding box with safe padding
        pad = 2
        x1 = max(0, token.pixel_bbox.x - pad)
        y1 = max(0, token.pixel_bbox.y - pad)
        x2 = min(img_w, token.pixel_bbox.x + token.pixel_bbox.width + pad)
        y2 = min(img_h, token.pixel_bbox.y + token.pixel_bbox.height + pad)

        if x2 - x1 < 4 or y2 - y1 < 4:
            return 0.0

        crop = gray_img[y1:y2, x1:x2]

        # Otsu thresholding to separate text foreground from background
        _, binary = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # In academic certificates text is usually dark on bright background.
        # If foreground ratio is > 70%, background was likely inverted
        fg_ratio = np.count_nonzero(binary) / binary.size
        if fg_ratio > 0.70:
            binary = cv2.bitwise_not(binary)

        fg_pixels = np.count_nonzero(binary)
        if fg_pixels < 10:
            return 0.0

        # Exact distance transform: for binary text, distance to nearest background pixel
        # The medial axis radius is half the stroke width, so stroke width = 2 * distance
        dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)

        # Consider pixels on the medial ridge (distance values where dist > 0.8px)
        ridge_pixels = dist[dist >= 0.8]
        if len(ridge_pixels) == 0:
            return 0.0

        # Calculate stroke width as twice the mean of top 70% ridge distances
        stroke_width = 2.0 * float(np.percentile(ridge_pixels, 75))
        return min(float(self.config.max_stroke_width_px), stroke_width)
