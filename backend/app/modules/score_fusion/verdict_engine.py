"""Verdict determination and confidence calibration engine."""

from __future__ import annotations

from typing import Tuple

from app.schemas.decision import VerificationVerdict
from app.schemas.primitives import RiskBand


class VerdictEngine:
    """Classifies authenticity scores into canonical project verdicts with calibrated confidence."""

    THRESHOLD_AUTHENTIC = 0.85
    THRESHOLD_SUSPICIOUS = 0.60

    @classmethod
    def evaluate(
        cls,
        authenticity_score: float,
        veto_applied: bool = False,
        veto_reason: str | None = None,
    ) -> Tuple[VerificationVerdict, RiskBand, float, str]:
        """Categorize authenticity score into Verdict, RiskBand, Confidence, and Rationale."""
        score = max(0.0, min(1.0, float(authenticity_score)))

        if score >= cls.THRESHOLD_AUTHENTIC:
            verdict = VerificationVerdict.AUTHENTIC
            risk_band = RiskBand.LOW
            # Confidence scales 0.70 to 1.00 as score approaches 1.0
            ratio = (score - cls.THRESHOLD_AUTHENTIC) / max(1e-6, 1.0 - cls.THRESHOLD_AUTHENTIC)
            confidence = 0.70 + 0.30 * ratio
            if veto_applied and veto_reason:
                rationale = (
                    f"Document confirmed authentic by authoritative verification: {veto_reason}"
                )
            else:
                rationale = (
                    f"Document exhibits high integrity across visual, text, and forensic analysis "
                    f"(Authenticity Score: {score * 100:.1f}%). Low risk of manipulation."
                )

        elif score >= cls.THRESHOLD_SUSPICIOUS:
            verdict = VerificationVerdict.SUSPICIOUS
            risk_band = RiskBand.MEDIUM
            # Inconclusive / uncertain zone (0.50 - 0.68)
            mid = (cls.THRESHOLD_AUTHENTIC + cls.THRESHOLD_SUSPICIOUS) / 2.0
            distance_from_mid = abs(score - mid) / (
                cls.THRESHOLD_AUTHENTIC - cls.THRESHOLD_SUSPICIOUS
            )
            confidence = 0.50 + 0.18 * distance_from_mid
            rationale = (
                f"Document has borderline indicators (Authenticity Score: {score * 100:.1f}%). "
                f"Minor anomalies detected; manual registrar inspection recommended."
            )

        else:
            verdict = VerificationVerdict.MANIPULATED
            risk_band = RiskBand.HIGH
            # Confidence scales 0.70 to 1.00 as score approaches 0.0
            ratio = (cls.THRESHOLD_SUSPICIOUS - score) / max(1e-6, cls.THRESHOLD_SUSPICIOUS)
            confidence = 0.70 + 0.30 * ratio
            if veto_applied and veto_reason:
                rationale = f"Document flagged fraudulent due to contradiction: {veto_reason}"
            else:
                rationale = (
                    f"Document flagged as fake with significant anomalies detected across "
                    f"analytical branches (Authenticity Score: {score * 100:.1f}%). High risk."
                )

        return verdict, risk_band, round(min(1.0, confidence), 4), rationale
