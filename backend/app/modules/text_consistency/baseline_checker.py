import math
from typing import List, Optional, Tuple

import numpy as np
from scipy.stats import theilslopes

from app.modules.ocr.spatial_analyzer import TextLine
from app.schemas.text_consistency import AnomalousRegion, AnomalyType, TextConsistencyConfig


class BaselineAlignmentAnalyzer:
    """Detects vertical text displacement and baseline drift anomalies in lines of text."""

    DESCENDERS = set("gjpqyQJ")

    def __init__(self, config: Optional[TextConsistencyConfig] = None):
        self.config = config or TextConsistencyConfig()

    def analyze(self, text_lines: List[TextLine]) -> Tuple[float, List[AnomalousRegion]]:
        """Fit baselines across text lines and identify tokens with abnormal vertical drift.

        Returns:
            Tuple of (baseline_alignment_score [0.0, 1.0], list of anomalous regions).
        """
        if not text_lines:
            return 1.0, []

        line_scores: List[float] = []
        anomalies: List[AnomalousRegion] = []

        for line in text_lines:
            if len(line.tokens) < self.config.min_tokens_for_baseline:
                continue

            line_score, line_anomalies = self._analyze_line(line)
            line_scores.append(line_score)
            anomalies.extend(line_anomalies)

        overall_score = float(np.mean(line_scores)) if line_scores else 1.0
        return max(0.0, min(1.0, overall_score)), anomalies

    def _analyze_line(self, line: TextLine) -> Tuple[float, List[AnomalousRegion]]:
        tokens = line.tokens

        # For baseline fitting, prefer tokens without descenders if at least 3 exist
        non_descender_pts = []
        all_x = []
        all_y = []

        for t in tokens:
            x_c = t.pixel_bbox.x + (t.pixel_bbox.width / 2.0)
            y_b = float(t.pixel_bbox.y + t.pixel_bbox.height)
            all_x.append(x_c)
            all_y.append(y_b)
            if not (set(t.text) & self.DESCENDERS):
                non_descender_pts.append((x_c, y_b))

        fit_pts = (
            non_descender_pts
            if len(non_descender_pts) >= 3
            else list(zip(all_x, all_y, strict=False))
        )
        fit_x = np.array([p[0] for p in fit_pts], dtype=np.float64)
        fit_y = np.array([p[1] for p in fit_pts], dtype=np.float64)

        # Fit robust linear baseline using Theil-Sen regression
        if len(fit_x) >= 3 and np.std(fit_x) > 1e-4:
            res = theilslopes(fit_y, fit_x)
            slope = float(res.slope)
            intercept = float(res.intercept)
        else:
            slope = 0.0
            intercept = float(np.median(fit_y))

        # Compute residuals with descender compensation
        all_x_arr = np.array(all_x, dtype=np.float64)
        all_y_arr = np.array(all_y, dtype=np.float64)
        expected_y = slope * all_x_arr + intercept

        raw_residuals = []
        effective_residuals = []

        for i, t in enumerate(tokens):
            y_b = all_y_arr[i]
            exp_y = expected_y[i]
            diff = y_b - exp_y  # positive = lower than baseline, negative = raised above
            has_desc = bool(set(t.text) & self.DESCENDERS)

            # If token is below baseline and contains descenders, allow normal descender drop
            if diff > 0 and has_desc:
                descender_allowance = 0.25 * float(t.pixel_bbox.height)
                eff_diff = max(0.0, diff - descender_allowance)
            else:
                eff_diff = abs(diff)

            raw_residuals.append(abs(diff))
            effective_residuals.append(eff_diff)

        eff_res_arr = np.array(effective_residuals, dtype=np.float64)

        # Robust standard deviation via Median Absolute Deviation (MAD)
        med_res = float(np.median(eff_res_arr))
        mad = float(np.median(np.abs(eff_res_arr - med_res)))
        robust_sigma = 1.4826 * mad

        threshold = max(
            self.config.baseline_residual_px_threshold,
            self.config.baseline_sigma_multiplier * robust_sigma,
        )

        line_anomalies: List[AnomalousRegion] = []
        for i, token in enumerate(tokens):
            res_val = effective_residuals[i]
            if res_val >= threshold and res_val >= self.config.baseline_residual_px_threshold:
                drift_dir = "above" if (all_y_arr[i] < expected_y[i]) else "below"
                severity = min(1.0, max(0.5, res_val / 10.0))
                desc = (
                    f"Token '{token.text}' deviates {res_val:.1f}px {drift_dir} expected "
                    f"baseline (threshold: {threshold:.1f}px)"
                )
                line_anomalies.append(
                    AnomalousRegion(
                        anomaly_type=AnomalyType.BASELINE_DRIFT,
                        severity=round(severity, 3),
                        description=desc,
                        bbox=token.bbox,
                        pixel_bbox=token.pixel_bbox,
                        token_text=token.text,
                    )
                )

        mean_eff_res = float(np.mean(effective_residuals)) if effective_residuals else 0.0
        line_score = math.exp(-mean_eff_res / 3.0)

        if line_anomalies:
            line_score *= max(0.2, 1.0 - (0.25 * len(line_anomalies)))

        return max(0.0, min(1.0, line_score)), line_anomalies
