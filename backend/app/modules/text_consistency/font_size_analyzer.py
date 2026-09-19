from typing import List, Optional, Tuple

import numpy as np

from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.text_consistency import AnomalousRegion, AnomalyType, TextConsistencyConfig


class FontSizeAnalyzer:
    """Analyzes token bounding box heights to detect font size and scale mismatches."""

    def __init__(self, config: Optional[TextConsistencyConfig] = None):
        self.config = config or TextConsistencyConfig()

    def analyze(self, text_lines: List[TextLine]) -> Tuple[float, List[AnomalousRegion]]:
        """Identify tokens whose bounding box heights deviate anomalously from surrounding text.

        Returns:
            Tuple of (font_size_consistency_score [0.0, 1.0], list of anomalous regions).
        """
        if not text_lines:
            return 1.0, []

        anomalies: List[AnomalousRegion] = []
        flagged_token_ids = set()

        # Step 1: Intra-line height ratio analysis
        for line in text_lines:
            tokens = [t for t in line.tokens if len(t.text.strip()) > 1]
            if len(tokens) < 2:
                continue

            heights = [t.pixel_bbox.height for t in tokens]
            median_h = float(np.median(heights))

            if median_h <= 0:
                continue

            for t in tokens:
                ratio = t.pixel_bbox.height / median_h
                is_anomalous = (
                    ratio > self.config.font_size_ratio_upper
                    or ratio < self.config.font_size_ratio_lower
                )

                if is_anomalous:
                    dev_pct = abs(ratio - 1.0) * 100.0
                    direction = "oversized" if ratio > 1.0 else "undersized"
                    severity = min(1.0, max(0.5, (dev_pct - 25.0) / 50.0))
                    desc = (
                        f"Token '{t.text}' is {direction} ({t.pixel_bbox.height}px vs line median "
                        f"{median_h:.1f}px, deviation: {dev_pct:.1f}%)"
                    )
                    token_key = (t.pixel_bbox.x, t.pixel_bbox.y, t.text)
                    if token_key not in flagged_token_ids:
                        flagged_token_ids.add(token_key)
                        anomalies.append(
                            AnomalousRegion(
                                anomaly_type=AnomalyType.FONT_SIZE_MISMATCH,
                                severity=round(severity, 3),
                                description=desc,
                                bbox=t.bbox,
                                pixel_bbox=t.pixel_bbox,
                                token_text=t.text,
                            )
                        )

        # Step 2: Typographic tier variance analysis
        tier_map = self._cluster_into_tiers(text_lines)
        for tier_name, tier_tokens in tier_map.items():
            if len(tier_tokens) < 4:
                continue

            tier_heights = np.array([t.pixel_bbox.height for t in tier_tokens], dtype=np.float64)
            tier_median = float(np.median(tier_heights))
            tier_std = float(np.std(tier_heights))

            if tier_std < 1.0:
                continue

            for t in tier_tokens:
                z_score = abs(t.pixel_bbox.height - tier_median) / tier_std
                if z_score > self.config.font_size_tier_sigma_threshold:
                    token_key = (t.pixel_bbox.x, t.pixel_bbox.y, t.text)
                    if token_key not in flagged_token_ids:
                        flagged_token_ids.add(token_key)
                        severity = min(1.0, max(0.5, (z_score - 2.0) / 3.0))
                        desc = (
                            f"Token '{t.text}' height ({t.pixel_bbox.height}px) deviates by "
                            f"{z_score:.2f} std from {tier_name} tier median ({tier_median:.1f}px)"
                        )
                        anomalies.append(
                            AnomalousRegion(
                                anomaly_type=AnomalyType.FONT_SIZE_MISMATCH,
                                severity=round(severity, 3),
                                description=desc,
                                bbox=t.bbox,
                                pixel_bbox=t.pixel_bbox,
                                token_text=t.text,
                            )
                        )

        # Step 3: Compute overall font size consistency score
        score = max(0.0, 1.0 - min(1.0, 0.25 * len(anomalies)))
        return round(score, 3), anomalies

    def _cluster_into_tiers(self, text_lines: List[TextLine]) -> dict:
        """Categorize tokens into typography tiers based on line median heights."""
        tiers = {
            "Header": [],
            "Declaration": [],
            "Particulars": [],
            "FinePrint": [],
        }

        for line in text_lines:
            tokens = [t for t in line.tokens if len(t.text.strip()) > 1]
            if not tokens:
                continue
            line_median = float(np.median([t.pixel_bbox.height for t in tokens]))

            if line_median >= 24.0:
                tiers["Header"].extend(tokens)
            elif line_median >= 16.0:
                tiers["Declaration"].extend(tokens)
            elif line_median >= 11.0:
                tiers["Particulars"].extend(tokens)
            else:
                tiers["FinePrint"].extend(tokens)

        return tiers
