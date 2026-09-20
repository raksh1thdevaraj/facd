"""Weighted late fusion engine blending branch probabilities and sub-scores."""

from __future__ import annotations

from typing import Dict, List, Tuple

from app.schemas.decision import SubScoresBreakdown
from app.schemas.pipeline import ContributingFactor


class WeightedLateFusion:
    """Calculates explainable composite authenticity and risk scores via weighted blending."""

    DEFAULT_WEIGHTS: Dict[str, float] = {
        "visual": 0.30,
        "tabular": 0.30,
        "forensic": 0.15,
        "text": 0.15,
        "template": 0.10,
    }

    def __init__(self, weights: Dict[str, float] | None = None) -> None:
        raw_weights = weights or self.DEFAULT_WEIGHTS
        total = sum(raw_weights.values())
        if total <= 0:
            raise ValueError("Sum of fusion weights must be positive")
        self.weights = {k: v / total for k, v in raw_weights.items()}

    def blend(
        self,
        visual_fake_prob: float,
        tabular_fake_prob: float,
        forensic_score: float,
        text_consistency_score: float,
        template_score: float,
    ) -> Tuple[float, float, SubScoresBreakdown, List[ContributingFactor]]:
        """Compute composite authenticity score [0.0, 1.0], risk score [0.0, 100.0],

        sub-score breakdown, and explainability contributing factors.
        """
        # Convert fake probabilities to authenticity scores [0.0 = Fake, 1.0 = Authentic]
        s_visual = max(0.0, min(1.0, 1.0 - float(visual_fake_prob)))
        s_tabular = max(0.0, min(1.0, 1.0 - float(tabular_fake_prob)))
        s_forensic = max(0.0, min(1.0, float(forensic_score)))
        s_text = max(0.0, min(1.0, float(text_consistency_score)))
        s_template = max(0.0, min(1.0, float(template_score)))

        sub_scores = SubScoresBreakdown(
            visual_branch_score=round(s_visual, 4),
            tabular_branch_score=round(s_tabular, 4),
            text_consistency_score=round(s_text, 4),
            forensic_score=round(s_forensic, 4),
            template_score=round(s_template, 4),
        )

        composite_authenticity = (
            self.weights["visual"] * s_visual
            + self.weights["tabular"] * s_tabular
            + self.weights["forensic"] * s_forensic
            + self.weights["text"] * s_text
            + self.weights["template"] * s_template
        )
        composite_authenticity = max(0.0, min(1.0, composite_authenticity))
        overall_risk = (1.0 - composite_authenticity) * 100.0

        # Construct ContributingFactor items
        factors = self._build_contributing_factors(sub_scores)

        return (
            round(composite_authenticity, 4),
            round(overall_risk, 2),
            sub_scores,
            factors,
        )

    def _build_contributing_factors(
        self, sub_scores: SubScoresBreakdown
    ) -> List[ContributingFactor]:
        mapping = [
            (
                "visual",
                "ML_MODEL",
                sub_scores.visual_branch_score,
                "Deep learning visual CNN texture analysis",
            ),
            (
                "tabular",
                "ML_MODEL",
                sub_scores.tabular_branch_score,
                "Statistical baseline machine learning model",
            ),
            (
                "forensic",
                "FORENSICS",
                sub_scores.forensic_score,
                "Classical forensic artifact analysis (ELA, clones)",
            ),
            (
                "text",
                "TEXT_CONSISTENCY",
                sub_scores.text_consistency_score,
                "Rule-based text & format consistency",
            ),
            (
                "template",
                "TEMPLATE",
                sub_scores.template_score,
                "Master template structure and seal alignment",
            ),
        ]

        factors: List[ContributingFactor] = []
        for key, category, score, desc in mapping:
            weight = self.weights[key] * 100.0
            # Higher risk impact if score is low
            if score < 0.50:
                impact = "HIGH"
            elif score < 0.75:
                impact = "MEDIUM"
            else:
                impact = "LOW"

            factors.append(
                ContributingFactor(
                    factor_id=f"factor_{key}",
                    category=category,
                    impact=impact,
                    weight_percentage=round(weight, 1),
                    description=f"{desc} (Authenticity: {score * 100:.1f}%)",
                )
            )

        # Sort by lowest authenticity score (highest risk drivers first)
        factors.sort(key=lambda f: float(f.description.split(": ")[-1].replace("%)", "")))
        return factors
