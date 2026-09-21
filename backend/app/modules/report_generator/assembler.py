"""Report assembler harvesting outputs across all pipeline analytical stages."""

from __future__ import annotations

import datetime
import uuid
from typing import List, Optional

from app.schemas.decision import FinalVerificationDecision
from app.schemas.explainability import ExplainabilityReport, FeatureAttribution, FindingBullet
from app.schemas.pipeline import CertificateFields
from app.schemas.report import (
    FileMetadata,
    FullVerificationReport,
    SubsystemScoreItem,
    VisualEvidencePaths,
)


class ReportAssembler:
    """Assembles inputs from all analytical pipeline phases into FullVerificationReport."""

    @classmethod
    def assemble(
        cls,
        certificate_id: str,
        decision: FinalVerificationDecision,
        file_metadata: Optional[FileMetadata] = None,
        extracted_fields: Optional[CertificateFields] = None,
        explainability_report: Optional[ExplainabilityReport] = None,
        visual_evidence: Optional[VisualEvidencePaths] = None,
        subsystem_scores: Optional[List[SubsystemScoreItem]] = None,
        report_id: Optional[str] = None,
        verifier_username: str = "System Autopilot",
        base_url: str = "http://localhost:8000",
    ) -> FullVerificationReport:
        """Harvest outputs across pipeline and construct FullVerificationReport."""
        rep_id = report_id or str(uuid.uuid4())
        gen_time = datetime.datetime.utcnow()

        # 1. File Metadata Fallback
        if file_metadata is None:
            file_metadata = FileMetadata(
                filename=f"{certificate_id}.png",
                file_size_kb=256.0,
                file_format="PNG",
                sha256_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                upload_timestamp=gen_time,
            )

        # 2. Extracted Fields Fallback
        if extracted_fields is None:
            extracted_fields = CertificateFields()

        # 3. Subsystem Scores Calculation
        if subsystem_scores is None:
            sub = decision.sub_scores
            subsystem_scores = [
                SubsystemScoreItem(
                    name="Visual AI (Deep CNN)",
                    score=round(sub.visual_branch_score, 4),
                    weight=0.30,
                    status="GENUINE"
                    if sub.visual_branch_score >= 0.70
                    else ("BORDERLINE" if sub.visual_branch_score >= 0.50 else "MANIPULATED"),
                    detail="CNN visual feature extraction & artifact analysis",
                ),
                SubsystemScoreItem(
                    name="Tabular Classifier (RF)",
                    score=round(sub.tabular_branch_score, 4),
                    weight=0.30,
                    status="GENUINE"
                    if sub.tabular_branch_score >= 0.70
                    else ("BORDERLINE" if sub.tabular_branch_score >= 0.50 else "MANIPULATED"),
                    detail="22D statistical, layout, and frequency features",
                ),
                SubsystemScoreItem(
                    name="Digital Image Forensics",
                    score=round(sub.forensic_score, 4),
                    weight=0.15,
                    status="PASSED" if sub.forensic_score >= 0.70 else "ANOMALOUS",
                    detail="Error Level Analysis, noise variance, and copy-move",
                ),
                SubsystemScoreItem(
                    name="Typography & OCR Consistency",
                    score=round(sub.text_consistency_score, 4),
                    weight=0.15,
                    status="PASSED" if sub.text_consistency_score >= 0.75 else "ANOMALOUS",
                    detail="Baseline alignment, stroke width, and kerning rules",
                ),
                SubsystemScoreItem(
                    name="Institutional Template Alignment",
                    score=round(sub.template_score, 4),
                    weight=0.10,
                    status="MATCHED" if sub.template_score >= 0.80 else "DEVIANT",
                    detail="Multi-scale structural similarity (SSIM) matching",
                ),
                SubsystemScoreItem(
                    name="Database Record Match (Tier)",
                    score=1.0
                    if "TIER_1" in decision.tier_status
                    else (0.7 if "TIER_2" in decision.tier_status else 0.0),
                    weight=0.00,  # Veto / Ground Truth
                    status=decision.tier_status,
                    detail=(
                        "Authoritative institutional ground-truth record check"
                        if not decision.veto_applied
                        else f"VETO TRIGGERED: {decision.veto_reason}"
                    ),
                ),
            ]

        # 4. Explainability & Findings Integration
        findings: List[FindingBullet] = []
        top_features: List[FeatureAttribution] = []
        exec_summary = decision.summary_rationale

        if explainability_report is not None:
            findings = getattr(
                explainability_report,
                "key_findings",
                getattr(explainability_report, "findings", []),
            )
            top_features = getattr(
                explainability_report,
                "top_contributing_features",
                getattr(explainability_report, "top_positive_features", [])
                + getattr(explainability_report, "top_negative_features", []),
            )
            summary_text = getattr(
                explainability_report,
                "primary_verdict_rationale",
                getattr(explainability_report, "summary_paragraph", None),
            )
            if summary_text:
                exec_summary = summary_text

        # 5. Visual Evidence Paths Integration
        if visual_evidence is None:
            visual_evidence = VisualEvidencePaths()
        overlay_p = (
            getattr(
                explainability_report,
                "unified_overlay_path",
                getattr(explainability_report, "overlay_image_path", None),
            )
            if explainability_report
            else None
        )
        if overlay_p and not visual_evidence.unified_overlay:
            visual_evidence.unified_overlay = overlay_p

        auth_pct = round(decision.overall_authenticity_score * 100.0, 1)
        verif_url = f"{base_url.rstrip('/')}/verify-report/{rep_id}"

        return FullVerificationReport(
            report_id=rep_id,
            certificate_id=certificate_id,
            generated_at=gen_time,
            verifier_username=verifier_username,
            file_metadata=file_metadata,
            verdict=decision.verdict,
            authenticity_score=round(decision.overall_authenticity_score, 4),
            authenticity_percentage=auth_pct,
            risk_score=round(decision.overall_risk_score, 1),
            risk_band=decision.risk_band,
            confidence_score=round(decision.confidence, 4),
            tier_status=decision.tier_status,
            veto_applied=decision.veto_applied,
            veto_reason=decision.veto_reason,
            executive_summary=exec_summary,
            extracted_fields=extracted_fields,
            subsystem_scores=subsystem_scores,
            findings=findings,
            top_features=top_features,
            visual_evidence=visual_evidence,
            verification_url=verif_url,
        )
