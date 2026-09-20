from app.modules.template_matching.tier_classifier import classify_tier
from app.schemas.template_matching import (
    RecordVerificationResult,
    TemplateMatchMetrics,
    TierStatus,
)


def test_tc_tmp_03_exact_record_yields_tier_1_verified():
    """TC-TMP-03: Confirmed record in database yields TIER_1_VERIFIED with 0.99 confidence."""
    record_result = RecordVerificationResult(
        record_found=True,
        matched_record_id="rec-123",
        name_match_score=0.95,
        roll_no_match=True,
        degree_match=True,
        passing_year_match=True,
        cgpa_match=True,
        discrepancies=[],
    )

    classification = classify_tier(record_result=record_result)

    assert classification.tier == TierStatus.TIER_1_VERIFIED
    assert classification.confidence >= 0.95
    assert "Authentic student graduation record confirmed" in classification.primary_reason


def test_tc_tmp_04_record_contradiction_yields_tier_3_inconsistent():
    """TC-TMP-04: Contradiction between cert and university record yields TIER_3_INCONSISTENT."""
    record_result = RecordVerificationResult(
        record_found=True,
        matched_record_id="rec-123",
        name_match_score=0.35,  # Contradicts!
        roll_no_match=True,
        degree_match=True,
        passing_year_match=True,
        cgpa_match=True,
        discrepancies=["Name on certificate contradicts record."],
    )

    classification = classify_tier(record_result=record_result)

    assert classification.tier == TierStatus.TIER_3_INCONSISTENT
    assert classification.confidence >= 0.90
    assert "contradict" in classification.primary_reason.lower()


def test_tc_tmp_04_low_template_score_yields_tier_3_inconsistent():
    """TC-TMP-04: Severely divergent template score (<0.60) yields TIER_3_INCONSISTENT."""
    record_result = RecordVerificationResult(record_found=False)
    template_metrics = TemplateMatchMetrics(
        ssim_score=0.45,
        feature_similarity_score=0.20,
        seal_match_score=0.30,
        overall_template_score=0.42,
        alignment_success=False,
    )

    classification = classify_tier(
        record_result=record_result,
        template_metrics=template_metrics,
    )

    assert classification.tier == TierStatus.TIER_3_INCONSISTENT
    assert (
        "deviate" in classification.primary_reason.lower()
        or "template" in classification.primary_reason.lower()
    )


def test_tc_tmp_05_unlisted_record_matching_template_yields_tier_2_consistent():
    """TC-TMP-05: Missing student record with matching master template yields TIER_2_CONSISTENT."""
    record_result = RecordVerificationResult(record_found=False)
    template_metrics = TemplateMatchMetrics(
        ssim_score=0.88,
        feature_similarity_score=0.82,
        seal_match_score=0.90,
        overall_template_score=0.87,
        alignment_success=True,
    )

    classification = classify_tier(
        record_result=record_result,
        template_metrics=template_metrics,
        forensic_score=0.85,
        text_score=0.90,
    )

    assert classification.tier == TierStatus.TIER_2_CONSISTENT
    assert classification.confidence >= 0.80
    assert "consistent" in classification.primary_reason.lower()


def test_fallback_unlisted_student_no_template_yields_tier_3_unverified():
    """Unlisted student without template yields TIER_3_UNVERIFIED fallback."""
    record_result = RecordVerificationResult(record_found=False)

    classification = classify_tier(
        record_result=record_result,
        template_metrics=None,
    )

    assert classification.tier == TierStatus.TIER_3_UNVERIFIED
