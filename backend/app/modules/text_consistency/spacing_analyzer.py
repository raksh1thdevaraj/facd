from typing import List, Optional, Tuple

import numpy as np

from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.pipeline import OCRToken
from app.schemas.primitives import BoundingBox, PixelBoundingBox
from app.schemas.text_consistency import AnomalousRegion, AnomalyType, TextConsistencyConfig


class CharacterSpacingAnalyzer:
    """Analyzes horizontal token spacing (kerning) and vertical line leading consistency."""

    def __init__(self, config: Optional[TextConsistencyConfig] = None):
        self.config = config or TextConsistencyConfig()

    def analyze(self, text_lines: List[TextLine]) -> Tuple[float, List[AnomalousRegion]]:
        """Identify token collisions, unnatural kerning gaps, and irregular line leading.

        Returns:
            Tuple of (spacing_consistency_score [0.0, 1.0], list of anomalous regions).
        """
        if not text_lines:
            return 1.0, []

        anomalies: List[AnomalousRegion] = []

        # Step 1: Inter-token horizontal gap analysis
        for line in text_lines:
            tokens = line.tokens
            if len(tokens) < 3:
                continue

            gaps: List[float] = []
            for i in range(len(tokens) - 1):
                t_curr = tokens[i]
                t_next = tokens[i + 1]
                gap = float(t_next.pixel_bbox.x - (t_curr.pixel_bbox.x + t_curr.pixel_bbox.width))
                gaps.append(gap)

            positive_gaps = [g for g in gaps if g > 0]
            median_gap = float(np.median(positive_gaps)) if positive_gaps else 8.0

            for i in range(len(tokens) - 1):
                gap = gaps[i]
                t_curr = tokens[i]
                t_next = tokens[i + 1]

                # 1. Collision / overlapping tokens
                if gap < -1.0:
                    severity = min(1.0, max(0.6, abs(gap) / 10.0))
                    desc = (
                        f"Collision/overlap between '{t_curr.text}' and '{t_next.text}' "
                        f"(overlap of {abs(gap):.1f}px)"
                    )
                    anomalies.append(
                        self._create_spacing_anomaly(
                            t_curr,
                            t_next,
                            severity=severity,
                            description=desc,
                        )
                    )

                # 2. Micro-compression (abnormally compressed kerning)
                elif median_gap >= 5.0 and gap < (
                    self.config.micro_gap_ratio_threshold * median_gap
                ):
                    severity = min(1.0, max(0.5, 1.0 - (gap / median_gap)))
                    desc = (
                        f"Compressed character gap ({gap:.1f}px vs line median {median_gap:.1f}px) "
                        f"between '{t_curr.text}' and '{t_next.text}'"
                    )
                    anomalies.append(
                        self._create_spacing_anomaly(
                            t_curr,
                            t_next,
                            severity=severity,
                            description=desc,
                        )
                    )

                # 3. Macro-gap (unnatural stretched tracking within sentence)
                elif (
                    median_gap >= 4.0
                    and gap > (self.config.macro_gap_ratio_threshold * median_gap)
                    and gap < 120.0  # Ignore large column indents
                ):
                    severity = min(1.0, max(0.4, (gap - 2.5 * median_gap) / (2.0 * median_gap)))
                    desc = (
                        f"Stretched gap ({gap:.1f}px vs median {median_gap:.1f}px) "
                        f"between '{t_curr.text}' and '{t_next.text}'"
                    )
                    anomalies.append(
                        self._create_spacing_anomaly(
                            t_curr,
                            t_next,
                            severity=severity,
                            description=desc,
                        )
                    )

        # Step 2: Vertical leading (line spacing regularity)
        leading_anomalies = self._analyze_line_leading(text_lines)
        anomalies.extend(leading_anomalies)

        # Step 3: Compute composite spacing consistency score
        score = max(0.0, 1.0 - min(1.0, 0.20 * len(anomalies)))
        return round(score, 3), anomalies

    def _analyze_line_leading(self, lines: List[TextLine]) -> List[AnomalousRegion]:
        """Detect irregular vertical gaps between successive lines of text."""
        if len(lines) < 3:
            return []

        sorted_lines = sorted(lines, key=lambda ln: ln.pixel_bbox.y)
        leadings: List[float] = []

        for i in range(len(sorted_lines) - 1):
            curr_bottom = sorted_lines[i].pixel_bbox.y + sorted_lines[i].pixel_bbox.height
            next_top = sorted_lines[i + 1].pixel_bbox.y
            leadings.append(float(next_top - curr_bottom))

        positive_leadings = [ld for ld in leadings if ld > 2.0]
        if len(positive_leadings) < 3:
            return []

        median_lead = float(np.median(positive_leadings))
        if median_lead <= 3.0:
            return []

        anomalies: List[AnomalousRegion] = []
        for i, lead in enumerate(leadings):
            rel_dev = abs(lead - median_lead) / median_lead
            if rel_dev > self.config.line_leading_deviation_threshold and lead < 150.0:
                line_obj = sorted_lines[i + 1]
                severity = min(1.0, max(0.5, rel_dev - 0.3))
                desc = (
                    f"Irregular line leading of {lead:.1f}px (median: {median_lead:.1f}px, "
                    f"deviation: {rel_dev * 100:.1f}%) above line: '{line_obj.text[:30]}...'"
                )
                anomalies.append(
                    AnomalousRegion(
                        anomaly_type=AnomalyType.SPACING_IRREGULARITY,
                        severity=round(severity, 3),
                        description=desc,
                        bbox=line_obj.bbox,
                        pixel_bbox=line_obj.pixel_bbox,
                        token_text=line_obj.text[:40],
                    )
                )

        return anomalies

    def _create_spacing_anomaly(
        self,
        t1: OCRToken,
        t2: OCRToken,
        severity: float,
        description: str,
    ) -> AnomalousRegion:
        """Create an anomalous region spanning the two interacting tokens."""
        min_x = min(t1.pixel_bbox.x, t2.pixel_bbox.x)
        min_y = min(t1.pixel_bbox.y, t2.pixel_bbox.y)
        max_r = max(t1.pixel_bbox.x + t1.pixel_bbox.width, t2.pixel_bbox.x + t2.pixel_bbox.width)
        max_b = max(t1.pixel_bbox.y + t1.pixel_bbox.height, t2.pixel_bbox.y + t2.pixel_bbox.height)

        pixel_box = PixelBoundingBox(
            x=min_x,
            y=min_y,
            width=max(1, max_r - min_x),
            height=max(1, max_b - min_y),
        )

        norm_box = BoundingBox(
            x1=min(t1.bbox.x1, t2.bbox.x1),
            y1=min(t1.bbox.y1, t2.bbox.y1),
            x2=max(t1.bbox.x2, t2.bbox.x2),
            y2=max(t1.bbox.y2, t2.bbox.y2),
        )

        return AnomalousRegion(
            anomaly_type=AnomalyType.SPACING_IRREGULARITY,
            severity=round(severity, 3),
            description=description,
            bbox=norm_box,
            pixel_bbox=pixel_box,
            token_text=f"{t1.text} | {t2.text}",
        )
