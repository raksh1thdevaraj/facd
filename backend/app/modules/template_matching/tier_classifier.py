from typing import Optional

from app.schemas.template_matching import (
    RecordVerificationResult,
    TemplateMatchMetrics,
    TierClassification,
    TierStatus,
)


def classify_tier(
    record_result: RecordVerificationResult,
    template_metrics: Optional[TemplateMatchMetrics] = None,
    forensic_score: float = 1.0,
    text_score: float = 1.0,
) -> TierClassification:
    """Classify certificate into Tier 1, Tier 2, or Tier 3 status.

    Args:
        record_result: Cross-verification results from institutional database.
        template_metrics: Optional visual metrics from master template comparison.
        forensic_score: Authenticity score from digital image forensics [0.0, 1.0].
        text_score: Authenticity score from typographical consistency [0.0, 1.0].

    Returns:
        TierClassification with assigned TierStatus, confidence, and human-readable explanation.
    """
    discrepancies = list(record_result.discrepancies)

    # Rule 1: Explicit Database Inconsistency -> Tier 3 Inconsistent
    if record_result.record_found:
        is_name_match = record_result.name_match_score >= 0.85
        has_major_mismatch = (
            not is_name_match
            or not record_result.roll_no_match
            or not record_result.degree_match
            or not record_result.cgpa_match
            or not record_result.passing_year_match
        )
        if has_major_mismatch:
            return TierClassification(
                tier=TierStatus.TIER_3_INCONSISTENT,
                confidence=0.95,
                primary_reason=(
                    "Certificate particulars contradict authentic student records "
                    "in the university database."
                ),
                discrepancies=discrepancies,
            )

    # Rule 2: Severe Visual Divergence / Counterfeit Template -> Tier 3 Inconsistent
    if template_metrics is not None and template_metrics.overall_template_score < 0.60:
        discrepancy_msg = (
            f"Certificate layout score ({template_metrics.overall_template_score:.2f}) "
            f"deviates severely from registered master template (threshold 0.60)."
        )
        if discrepancy_msg not in discrepancies:
            discrepancies.append(discrepancy_msg)
        return TierClassification(
            tier=TierStatus.TIER_3_INCONSISTENT,
            confidence=0.90,
            primary_reason=(
                "Visual layout, seal, or borders deviate substantially from master template."
            ),
            discrepancies=discrepancies,
        )

    # Rule 3: Ground-Truth Match -> Tier 1 (Verified)
    if (
        record_result.record_found
        and record_result.name_match_score >= 0.85
        and record_result.roll_no_match
    ):
        return TierClassification(
            tier=TierStatus.TIER_1_VERIFIED,
            confidence=0.99,
            primary_reason=(
                "Authentic student graduation record confirmed in official university database."
            ),
            discrepancies=[],
        )

    # Rule 4: Visual & Typographic Consistency -> Tier 2 (Consistent)
    # Record not found, but layout matches master template and no forensic anomalies
    if (
        template_metrics is not None
        and template_metrics.overall_template_score >= 0.80
        and forensic_score >= 0.70
        and text_score >= 0.70
    ):
        return TierClassification(
            tier=TierStatus.TIER_2_CONSISTENT,
            confidence=0.85,
            primary_reason=(
                "Certificate layout, seal, and typography are consistent with master template; "
                "individual student record not present in database archive."
            ),
            discrepancies=discrepancies,
        )

    # Rule 5: Fallback -> Tier 3 (Unverified)
    return TierClassification(
        tier=TierStatus.TIER_3_UNVERIFIED,
        confidence=0.70,
        primary_reason=(
            "No registered institutional student record or authentic master template "
            "available for authoritative verification."
        ),
        discrepancies=discrepancies,
    )
