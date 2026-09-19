from typing import List, Tuple

from app.schemas.pipeline import ConsistencyCheckItem
from app.schemas.primitives import CheckStatus
from app.schemas.text_consistency import (
    AnomalousRegion,
    AnomalyType,
    TextConsistencyConfig,
)


class ScoreAggregator:
    """Combines individual typographical, spacing, formatting, and logical sub-scores
    into a unified, explainable text consistency score with veto penalties for critical tampering.
    """

    def __init__(self, config: TextConsistencyConfig):
        self.config = config

    def aggregate(
        self,
        baseline_score: float,
        font_size_score: float,
        stroke_weight_score: float,
        spacing_score: float,
        format_score: float,
        logical_score: float,
        anomalies: List[AnomalousRegion],
        existing_checks: List[ConsistencyCheckItem],
    ) -> Tuple[float, List[ConsistencyCheckItem]]:
        """Compute the weighted composite score, enforce veto penalties, and assemble audit checks.

        Returns:
            Tuple of (overall_text_consistency_score [0.0, 1.0], list of ConsistencyCheckItem).
        """
        # Weighted raw score
        raw_score = (
            self.config.weight_baseline * baseline_score
            + self.config.weight_font_size * font_size_score
            + self.config.weight_stroke_weight * stroke_weight_score
            + self.config.weight_spacing * spacing_score
            + self.config.weight_logical * logical_score
        )

        # Incorporate format score as a minor dampener
        if format_score < 1.0:
            raw_score *= max(0.60, format_score)

        # Veto Penalty 1: Critical logical contradiction caps score at 0.40
        has_critical_logic_error = any(
            a.anomaly_type == AnomalyType.LOGICAL_CONTRADICTION and a.severity >= 0.90
            for a in anomalies
        )
        if has_critical_logic_error:
            raw_score = min(raw_score, 0.40)

        # Veto Penalty 2: Multiple high-severity typographical tampering anomalies
        high_severity_anomalies = [a for a in anomalies if a.severity >= 0.75]
        if len(high_severity_anomalies) >= 3:
            penalty_factor = 0.85 ** (len(high_severity_anomalies) - 2)
            raw_score *= penalty_factor

        overall_score = max(0.0, min(1.0, raw_score))

        # Build comprehensive rule checks
        checks = list(existing_checks)

        # Baseline Alignment Rule
        baseline_count = sum(1 for a in anomalies if a.anomaly_type == AnomalyType.BASELINE_DRIFT)
        checks.append(
            ConsistencyCheckItem(
                rule_id="RULE_BASELINE_ALIGNMENT",
                name="Baseline Alignment & Drift",
                status=self._score_to_status(baseline_score),
                confidence=1.0,
                details=(
                    "Baselines are aligned across lines without significant vertical drift."
                    if baseline_score >= 0.85
                    else f"Detected vertical baseline drift in {baseline_count} tokens."
                ),
            )
        )

        # Font Size Rule
        font_count = sum(1 for a in anomalies if a.anomaly_type == AnomalyType.FONT_SIZE_MISMATCH)
        checks.append(
            ConsistencyCheckItem(
                rule_id="RULE_FONT_SIZE_CONSISTENCY",
                name="Font Size & Height Consistency",
                status=self._score_to_status(font_size_score),
                confidence=1.0,
                details=(
                    "Font sizes are uniform across lines and typographical tiers."
                    if font_size_score >= 0.85
                    else f"Found {font_count} tokens with anomalous font heights."
                ),
            )
        )

        # Stroke Weight Rule
        stroke_count = sum(
            1 for a in anomalies if a.anomaly_type == AnomalyType.STROKE_WEIGHT_DISCREPANCY
        )
        checks.append(
            ConsistencyCheckItem(
                rule_id="RULE_STROKE_WEIGHT_SWT",
                name="Stroke Width & Weight Transform",
                status=self._score_to_status(stroke_weight_score),
                confidence=1.0,
                details=(
                    "Character stroke widths are uniform with no mismatched bold/thin insertions."
                    if stroke_weight_score >= 0.85
                    else f"Detected {stroke_count} tokens with stroke weight anomalies."
                ),
            )
        )

        # Spacing / Kerning Rule
        spacing_count = sum(
            1 for a in anomalies if a.anomaly_type == AnomalyType.SPACING_IRREGULARITY
        )
        checks.append(
            ConsistencyCheckItem(
                rule_id="RULE_SPACING_KERNING",
                name="Character Spacing & Line Leading",
                status=self._score_to_status(spacing_score),
                confidence=1.0,
                details=(
                    "Inter-token spacing and vertical line leading conform to normal typography."
                    if spacing_score >= 0.85
                    else f"Detected {spacing_count} spacing or line leading irregularities."
                ),
            )
        )

        # Text Format & Script Rule
        format_count = sum(
            1 for a in anomalies if a.anomaly_type == AnomalyType.FORMAT_IRREGULARITY
        )
        checks.append(
            ConsistencyCheckItem(
                rule_id="RULE_TEXT_FORMAT_SCRIPT",
                name="Unicode Script & Format Regularity",
                status=self._score_to_status(format_score),
                confidence=1.0,
                details=(
                    "No homoglyphs or erratic casing artifacts detected."
                    if format_score >= 0.85
                    else f"Identified {format_count} formatting or script inconsistencies."
                ),
            )
        )

        return round(overall_score, 3), checks

    def _score_to_status(self, score: float) -> CheckStatus:
        if score >= 0.85:
            return CheckStatus.PASSED
        elif score >= 0.65:
            return CheckStatus.WARNING
        return CheckStatus.FAILED
