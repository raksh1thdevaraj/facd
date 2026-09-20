"""Institutional Veto Override Engine for authoritative ground-truth rules."""

from __future__ import annotations

from typing import List, Optional, Tuple, Union

from app.schemas.template_matching import TierStatus


class InstitutionalVetoEngine:
    """Applies definitive database ground-truth overrides to statistical AI scores."""

    @staticmethod
    def apply_vetoes(
        raw_authenticity_score: float,
        tier_status: Union[str, TierStatus],
        record_found: bool = False,
        discrepancies: Optional[List[str]] = None,
        primary_reason: Optional[str] = None,
    ) -> Tuple[float, bool, Optional[str]]:
        """Apply authoritative institutional ground-truth overrides.

        Returns:
            Tuple of (adjusted_authenticity_score, veto_applied, veto_reason)
        """
        score = max(0.0, min(1.0, float(raw_authenticity_score)))
        tier_str = tier_status.value if isinstance(tier_status, TierStatus) else str(tier_status)
        disc_list = discrepancies or []

        # =========================================================================
        # VETO 1: Definitive Inconsistency -> Force to MANIPULATED
        # =========================================================================
        if tier_str == TierStatus.TIER_3_INCONSISTENT.value:
            if record_found and disc_list:
                veto_score = min(score, 0.15)
                reason = (
                    f"CRITICAL VETO: Certificate details contradict official university "
                    f"database record ({disc_list[0]})."
                )
                return veto_score, True, reason

            if primary_reason and (
                "counterfeit" in primary_reason.lower()
                or "mismatched template" in primary_reason.lower()
            ):
                veto_score = min(score, 0.25)
                reason = (
                    "CRITICAL VETO: Certificate visual structure contradicts registered "
                    "university master template."
                )
                return veto_score, True, reason

            # General Tier 3 contradiction
            veto_score = min(score, 0.20)
            reason = "CRITICAL VETO: Institutional verification failed with discrepancies."
            return veto_score, True, reason

        # =========================================================================
        # VETO 2: Ground-Truth Match -> Boost to AUTHENTIC
        # =========================================================================
        if tier_str == TierStatus.TIER_1_VERIFIED.value:
            veto_score = max(score, 0.95)
            reason = "CONFIRMATION VETO: Exact student record match verified in university records."
            return veto_score, True, reason

        # =========================================================================
        # No Veto: Tier 2 Consistent or Tier 3 Unverified (Maintain statistical score)
        # =========================================================================
        return score, False, None
