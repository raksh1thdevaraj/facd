"""Pydantic V2 schemas for verification reports, archival models, and report summaries."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.decision import VerificationVerdict
from app.schemas.explainability import FeatureAttribution, FindingBullet
from app.schemas.pipeline import CertificateFields, ContributingFactor, VerificationReportDTO
from app.schemas.primitives import RiskBand


class FileMetadata(BaseModel):
    """Cryptographic and filesystem metadata for the assessed certificate."""

    filename: str = Field(..., description="Original filename")
    file_size_kb: float = Field(..., ge=0.0, description="File size in kilobytes")
    file_format: str = Field(..., description="File MIME or extension (e.g. PNG, PDF)")
    sha256_checksum: str = Field(..., description="SHA-256 cryptographic digest of document")
    upload_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Upload timestamp"
    )


class SubsystemScoreItem(BaseModel):
    """Granular score entry for an analytical pipeline subsystem."""

    name: str = Field(..., description="Subsystem display name")
    score: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized score [0.0 = Fake, 1.0 = Genuine]"
    )
    weight: float = Field(..., ge=0.0, le=1.0, description="Fusion contribution weight")
    status: str = Field(..., description="Subsystem status (e.g., PASSED, WARNING, FAILED)")
    detail: str = Field(..., description="Key technical finding summary")


class VisualEvidencePaths(BaseModel):
    """Filesystem paths or URLs to rendered visual evidence plates."""

    original_image: Optional[str] = Field(
        default=None, description="Path to original document image"
    )
    unified_overlay: Optional[str] = Field(
        default=None, description="Path to unified multi-layer anomaly overlay"
    )
    forensic_heatmap: Optional[str] = Field(
        default=None, description="Path to ELA/Noise forensic heatmap"
    )
    gradcam_heatmap: Optional[str] = Field(
        default=None, description="Path to deep learning attention / Grad-CAM heatmap"
    )


class FullVerificationReport(BaseModel):
    """Complete comprehensive verification dossier covering all analytical branches."""

    report_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique verification report UUID"
    )
    certificate_id: str = Field(..., description="Assessed certificate identifier")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Report generation timestamp"
    )
    verifier_username: str = Field(
        default="System Autopilot", description="Operator or auditor identity"
    )
    file_metadata: FileMetadata = Field(..., description="Assessed file metadata")

    # Executive Verdict
    verdict: VerificationVerdict = Field(..., description="Categorical authenticity verdict")
    authenticity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Fused authenticity score [0.0 to 1.0]"
    )
    authenticity_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Authenticity formatted as percentage [0% to 100%]"
    )
    risk_score: float = Field(
        ..., ge=0.0, le=100.0, description="Calculated risk score [0.0 to 100.0]"
    )
    risk_band: RiskBand = Field(..., description="Risk category: LOW, MEDIUM, HIGH")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence level")
    tier_status: str = Field(
        default="TIER_3_UNVERIFIED", description="Authoritative registrar match tier"
    )
    veto_applied: bool = Field(default=False, description="True if institutional veto triggered")
    veto_reason: Optional[str] = Field(default=None, description="Veto rationale if triggered")
    executive_summary: str = Field(..., description="2-3 sentence executive verdict narrative")

    # Granular Findings
    extracted_fields: CertificateFields = Field(
        default_factory=CertificateFields, description="Extracted academic credentials"
    )
    subsystem_scores: List[SubsystemScoreItem] = Field(
        default_factory=list, description="Subsystem analytical score breakdown"
    )
    findings: List[FindingBullet] = Field(
        default_factory=list, description="Categorized natural language findings"
    )
    top_features: List[FeatureAttribution] = Field(
        default_factory=list, description="Top SHAP feature attributions"
    )

    # Evidence & Archival Links
    visual_evidence: VisualEvidencePaths = Field(
        default_factory=VisualEvidencePaths, description="Paths to visual evidence plates"
    )
    report_hmac_signature: Optional[str] = Field(
        default=None, description="HMAC-SHA256 digital signature of canonical report data"
    )
    verification_url: Optional[str] = Field(
        default=None, description="Public URL to verify digital authenticity of report"
    )
    qr_code_path: Optional[str] = Field(default=None, description="Filesystem path to QR image")
    pdf_path: Optional[str] = Field(default=None, description="Filesystem path to compiled PDF")
    json_path: Optional[str] = Field(
        default=None, description="Filesystem path to saved JSON report"
    )
    disclaimer: str = Field(
        default=(
            "Notice: This authenticity report is generated by an AI-assisted academic "
            "verification system using automated forensics, OCR, and institutional record "
            "matching. It is intended to assist admissions officers and employers. Final "
            "confirmation of academic credentials remains with the issuing institution."
        ),
        description="Legal and compliance disclaimer",
    )

    def to_dto(self) -> VerificationReportDTO:
        """Export to SPEC-02 canonical VerificationReportDTO."""
        from app.schemas.pipeline import (
            ForensicsOutput,
            MLInferenceOutput,
            TextConsistencyOutput,
        )

        contributing = [
            ContributingFactor(
                factor_id=f"feat_{i}",
                category="ML_MODEL",
                impact="HIGH" if abs(f.shap_value) > 0.1 else "MEDIUM",
                weight_percentage=round(abs(f.shap_value) * 100, 2),
                description=f"{f.feature_name}: {f.impact_direction}",
            )
            for i, f in enumerate(self.top_features[:5])
        ]

        from app.schemas.primitives import CheckStatus

        return VerificationReportDTO(
            verification_id=self.report_id,
            document_id=self.certificate_id,
            timestamp=self.generated_at.isoformat(),
            verifier_username=self.verifier_username,
            risk_score=round(self.risk_score, 2),
            risk_band=self.risk_band,
            extracted_fields=self.extracted_fields,
            consistency_results=TextConsistencyOutput(
                document_id=self.certificate_id,
                overall_status=(
                    CheckStatus.PASSED
                    if self.verdict == VerificationVerdict.AUTHENTIC
                    else CheckStatus.FAILED
                ),
                consistency_risk_score=round(100.0 - self.authenticity_percentage, 1),
                checks=[],
            ),
            forensics_results=ForensicsOutput(
                document_id=self.certificate_id,
                ela_heatmap_path=self.visual_evidence.forensic_heatmap or "",
                ela_score=0.1 if self.verdict == VerificationVerdict.AUTHENTIC else 0.8,
                copy_move_detected=False,
                copy_move_clusters_count=0,
                copy_move_score=0.0,
                font_irregularity_score=0.1,
                noise_inconsistency_score=0.1,
                forensics_risk_score=round(self.risk_score, 1),
                suspicious_regions=[],
            ),
            template_results=None,
            ml_results=MLInferenceOutput(
                model_version="v1.0",
                model_type="fused_multimodal",
                manipulation_probability=round(1.0 - self.authenticity_score, 4),
                predicted_class=(
                    "genuine" if self.verdict == VerificationVerdict.AUTHENTIC else "manipulated"
                ),
                feature_contributions={f.feature_name: f.shap_value for f in self.top_features},
                gradcam_heatmap_path=self.visual_evidence.gradcam_heatmap,
            ),
            contributing_factors=contributing,
            summary_verdict=self.verdict.value,
            disclaimer=self.disclaimer,
        )


class ReportSummary(BaseModel):
    """Lightweight summary schema for report search listings and web dashboards."""

    report_id: str
    certificate_id: str
    verdict: VerificationVerdict
    authenticity_score: float
    risk_band: RiskBand
    generated_at: datetime
    pdf_url: Optional[str] = None
    json_url: Optional[str] = None
