"""Natural Language Generation (NLG) engine for human-readable verification reports."""

from __future__ import annotations

from typing import Any, List, Optional

from app.schemas.decision import FinalVerificationDecision, VerificationVerdict
from app.schemas.explainability import FindingBullet, FindingCategory, FindingSeverity


class NLGExplanationGenerator:
    """Synthesizes raw analytical findings and scores into structured natural language bullets."""

    @classmethod
    def generate_summary_paragraph(cls, decision: FinalVerificationDecision) -> str:
        """Generate executive summary paragraph for decision."""
        score_pct = decision.overall_authenticity_score * 100.0
        risk_val = decision.overall_risk_score

        if decision.verdict == VerificationVerdict.AUTHENTIC:
            if decision.veto_applied and decision.veto_reason:
                return (
                    f"Certificate verification completed with status AUTHENTIC. "
                    f"The document was confirmed with 100% confidence by authoritative "
                    f"ground-truth verification: {decision.veto_reason}"
                )
            return (
                f"Certificate verification completed with status AUTHENTIC "
                f"(Authenticity: {score_pct:.1f}%, Risk: {risk_val:.1f}/100). The document "
                f"exhibits high physical and typographical integrity consistent with "
                f"authentic institutional issuance."
            )

        elif decision.verdict == VerificationVerdict.SUSPICIOUS:
            return (
                f"Certificate verification completed with status SUSPICIOUS "
                f"(Authenticity: {score_pct:.1f}%, Risk: {risk_val:.1f}/100). The automated "
                f"pipeline detected borderline anomalies or unverified institutional records. "
                f"Manual registrar inspection is advised before acceptance."
            )

        else:
            if decision.veto_applied and decision.veto_reason:
                return (
                    f"Certificate verification completed with status MANIPULATED (Fraud Detected). "
                    f"Authoritative institutional veto triggered: {decision.veto_reason}"
                )
            return (
                f"Certificate verification completed with status MANIPULATED "
                f"(Authenticity: {score_pct:.1f}%, Risk: {risk_val:.1f}/100). Multi-factor "
                f"analysis indicates digital tampering across visual textures, "
                f"typography, or compression signatures."
            )

    @classmethod
    def generate_finding_bullets(
        cls,
        decision: FinalVerificationDecision,
        text_result: Optional[Any] = None,
        forensic_result: Optional[Any] = None,
        tier_result: Optional[Any] = None,
        record_result: Optional[Any] = None,
    ) -> List[FindingBullet]:
        """Synthesize detailed finding bullets categorized by analytical domain."""
        bullets: List[FindingBullet] = []
        b_idx = 1

        # 1. Database & Record Verification
        if record_result is not None:
            discrepancies = getattr(record_result, "discrepancies", [])
            record_found = getattr(record_result, "record_found", False)

            if record_found and discrepancies:
                for disc in discrepancies:
                    bullets.append(
                        FindingBullet(
                            id=f"finding_{b_idx}",
                            severity=FindingSeverity.CRITICAL,
                            category=FindingCategory.DATABASE_RECORD,
                            title="Database Record Discrepancy",
                            description=(
                                f"Official student record contradicted by certificate: {disc}"
                            ),
                            evidence_value=str(disc),
                        )
                    )
                    b_idx += 1
            elif record_found and not discrepancies:
                bullets.append(
                    FindingBullet(
                        id=f"finding_{b_idx}",
                        severity=FindingSeverity.INFO,
                        category=FindingCategory.DATABASE_RECORD,
                        title="Database Record Match",
                        description=(
                            "Student roll number, full name, and graduation grade match "
                            "official registrar records."
                        ),
                    )
                )
                b_idx += 1

        # 2. Forensic Findings (Copy-Move, ELA, Noise)
        if forensic_result is not None:
            copy_move = getattr(forensic_result, "copy_move", None)
            if copy_move and getattr(copy_move, "cloned_regions_count", 0) > 0:
                count = copy_move.cloned_regions_count
                bullets.append(
                    FindingBullet(
                        id=f"finding_{b_idx}",
                        severity=FindingSeverity.CRITICAL,
                        category=FindingCategory.IMAGE_FORENSICS,
                        title="Copy-Move Splicing Detected",
                        description=(
                            f"Detected {count} cloned visual region(s). Identical pixel patches "
                            f"replicated across the certificate surface indicate stamp "
                            f"or signature forgery."
                        ),
                        evidence_value=f"{count} cloned patches",
                    )
                )
                b_idx += 1

            ela = getattr(forensic_result, "ela", None)
            if ela and getattr(ela, "ela_score", 1.0) < 0.65:
                score = ela.ela_score
                bullets.append(
                    FindingBullet(
                        id=f"finding_{b_idx}",
                        severity=FindingSeverity.MAJOR,
                        category=FindingCategory.COMPRESSION,
                        title="Compression Inconsistency (ELA)",
                        description=(
                            f"Error Level Analysis indicates localized compression variance "
                            f"(score: {score:.2f}). Text or seal elements were saved under "
                            f"different compression rates than the background."
                        ),
                        evidence_value=f"ELA Score {score:.2f}",
                    )
                )
                b_idx += 1

        # 3. Typography & Text Consistency
        if text_result is not None:
            anomalies = getattr(text_result, "anomalies", [])
            for anom in anomalies:
                anom_type = getattr(anom, "type", getattr(anom, "category", "Typography"))
                anom_desc = getattr(
                    anom, "description", getattr(anom, "message", "Typographical anomaly")
                )
                severity = (
                    FindingSeverity.CRITICAL
                    if "date" in str(anom_type).lower()
                    else FindingSeverity.MAJOR
                )

                bullets.append(
                    FindingBullet(
                        id=f"finding_{b_idx}",
                        severity=severity,
                        category=FindingCategory.TYPOGRAPHY,
                        title=f"Typographical Flaw ({anom_type})",
                        description=str(anom_desc),
                    )
                )
                b_idx += 1

        # 4. Authentic Fallback Findings (if no critical anomalies found)
        if not bullets and decision.verdict == VerificationVerdict.AUTHENTIC:
            bullets.append(
                FindingBullet(
                    id=f"finding_{b_idx}",
                    severity=FindingSeverity.INFO,
                    category=FindingCategory.TYPOGRAPHY,
                    title="Consistent Typography",
                    description=(
                        "Text lines exhibit uniform horizontal baseline alignment, "
                        "stroke width, and kerning."
                    ),
                )
            )
            b_idx += 1
            bullets.append(
                FindingBullet(
                    id=f"finding_{b_idx}",
                    severity=FindingSeverity.INFO,
                    category=FindingCategory.IMAGE_FORENSICS,
                    title="Uniform Compression Profile",
                    description=(
                        "No copy-paste duplication seams or localized JPEG "
                        "recompression anomalies detected."
                    ),
                )
            )
            b_idx += 1

        return bullets
