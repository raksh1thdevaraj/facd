"""Course Certificate Authenticity Verification Report Generator.

Generates both comprehensive JSON verification payloads and publication-grade
ReportLab PDF verification certificates with multi-signal evidence cards.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.modules.report_generator.pdf_styles import (
    COLOR_AUTHENTIC_BG,
    COLOR_AUTHENTIC_FG,
    COLOR_BORDER,
    COLOR_INDIGO,
    COLOR_LIGHT_BG,
    COLOR_MANIPULATED_BG,
    COLOR_MANIPULATED_FG,
    COLOR_NAVY,
    COLOR_SUSPICIOUS_BG,
    COLOR_SUSPICIOUS_FG,
    NumberedCanvas,
    get_report_styles,
)
from app.schemas.course_certificate import (
    CourseVerificationResponse,
    CourseVerificationStatus,
)

logger = logging.getLogger(__name__)

COLOR_GRAY_BG = HexColor("#F1F5F9")
COLOR_GRAY_FG = HexColor("#475569")


class CourseReportGenerator:
    """Generates JSON and PDF verification reports for course certificates."""

    def __init__(self) -> None:
        self.styles = get_report_styles()
        if "Subtitle" not in self.styles:
            if "ReportSubtitle" in self.styles:
                self.styles.add(ParagraphStyle("Subtitle", parent=self.styles["ReportSubtitle"]))
            else:
                self.styles.add(
                    ParagraphStyle("Subtitle", parent=self.styles["Normal"], fontSize=9, leading=12)
                )
        if "Muted" not in self.styles:
            self.styles.add(
                ParagraphStyle(
                    "Muted",
                    parent=self.styles["Normal"],
                    fontSize=8,
                    leading=10,
                    textColor=HexColor("#64748B"),
                )
            )

    def generate_json_summary(self, result: CourseVerificationResponse) -> dict[str, Any]:
        """Produce structured verification summary dictionary."""
        return {
            "certificate_id": result.certificate_id,
            "filename": result.filename,
            "verification_status": result.decision.status.value,
            "authenticity_score": result.decision.overall_authenticity_score,
            "fraud_risk_score": result.decision.fraud_risk_score,
            "verified_at": result.verified_at.isoformat(),
            "extracted_fields": result.extracted_fields.model_dump(),
            "qr_result": result.qr_result.model_dump(),
            "url_verification": result.url_result.model_dump(),
            "record_comparison": result.comparison_result.model_dump(),
            "pixel_forensics": result.forensic_result.model_dump(),
            "seal_signature": result.seal_signature_result.model_dump()
            if result.seal_signature_result
            else None,
            "decision_reasons": result.decision.decision_reasons,
            "risk_factors": result.decision.risk_factors,
            "signal_scores": result.decision.signal_scores,
        }

    def generate_pdf(
        self,
        result: CourseVerificationResponse,
        output_path: Path | None = None,
    ) -> bytes:
        """Render publication-grade PDF report for a course certificate verification."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            str(output_path) if output_path else buffer,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=40,
            bottomMargin=40,
        )

        elements = []
        status = result.decision.status

        # 1. Header Banner
        header_table = Table(
            [
                [
                    Paragraph(
                        "<b>ACADEMIC & COURSE CERTIFICATE FRAUD DETECTION SYSTEM</b>",
                        self.styles["Subtitle"],
                    ),
                    Paragraph(
                        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                        self.styles["Muted"],
                    ),
                ],
                [
                    Paragraph(
                        "<b>Course Authenticity Verification Audit Report</b>", self.styles["Title"]
                    ),
                    Paragraph(
                        f"Ref ID: <b>{result.certificate_id or 'N/A'}</b>", self.styles["Normal"]
                    ),
                ],
            ],
            colWidths=[360, 160],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                ]
            )
        )
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=1.5, color=COLOR_NAVY, spaceAfter=14))

        # 2. Verdict Banner
        if status == CourseVerificationStatus.VERIFIED:
            bg_col = COLOR_AUTHENTIC_BG
            fg_col = COLOR_AUTHENTIC_FG
            status_title = "VERIFIED - AUTHENTIC COURSE CERTIFICATE"
            status_desc = (
                "Multi-signal analysis confirms that this certificate matches "
                "authoritative issuer records with zero indications of tampering."
            )
        elif status == CourseVerificationStatus.SUSPICIOUS:
            bg_col = COLOR_SUSPICIOUS_BG
            fg_col = COLOR_SUSPICIOUS_FG
            status_title = "SUSPICIOUS - DISCREPANCIES DETECTED"
            status_desc = (
                "Minor discrepancies, unknown issuer domain, or inconclusive "
                "forensic anomalies detected. Manual review advised."
            )
        elif status == CourseVerificationStatus.FRAUDULENT:
            bg_col = COLOR_MANIPULATED_BG
            fg_col = COLOR_MANIPULATED_FG
            status_title = "FRAUDULENT - MANIPULATION / ATTACK CONFIRMED"
            status_desc = (
                "High-confidence tampering detected, such as copied QR code, "
                "unauthorized field modifications, or malicious URL."
            )
        else:
            bg_col = COLOR_GRAY_BG
            fg_col = COLOR_GRAY_FG
            status_title = "UNVERIFIED - VERIFICATION UNAVAILABLE"
            status_desc = (
                "Online registry could not be reached, or certificate does not "
                "contain machine-verifiable online credentials."
            )

        auth_score_text = f"{result.decision.overall_authenticity_score * 100:.1f}%"
        fraud_score_text = f"{result.decision.fraud_risk_score * 100:.1f}%"

        verdict_table = Table(
            [
                [
                    Paragraph(
                        f"<b><font size=14 color='{fg_col.hexval()}'>{status_title}</font></b>",
                        self.styles["Normal"],
                    ),
                ],
                [
                    Paragraph(status_desc, self.styles["Normal"]),
                ],
                [
                    Paragraph(
                        f"Authenticity Score: <b>{auth_score_text}</b> &nbsp;|&nbsp; "
                        f"Fraud Risk Score: <b>{fraud_score_text}</b>",
                        self.styles["Normal"],
                    )
                ],
            ],
            colWidths=[520],
        )
        verdict_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), bg_col),
                    ("BOX", (0, 0), (-1, -1), 1.5, fg_col),
                    ("PADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
                ]
            )
        )
        elements.append(verdict_table)
        elements.append(Spacer(1, 14))

        # 3. Certificate Details & Extracted Fields
        elements.append(Paragraph("<b>Extracted Certificate Metadata</b>", self.styles["Heading2"]))
        ext = result.extracted_fields
        meta_data = [
            [
                "Candidate Name:",
                ext.candidate_name or "Not Extracted",
                "Course Name:",
                ext.course_name or "Not Extracted",
            ],
            [
                "Issuer:",
                ext.issuer or "Unknown",
                "Certificate ID:",
                ext.certificate_id or "Not Extracted",
            ],
            [
                "Issue Date:",
                ext.issue_date or "Not Extracted",
                "OCR Confidence:",
                f"{ext.ocr_confidence * 100:.1f}%",
            ],
        ]
        meta_table = Table(meta_data, colWidths=[100, 160, 100, 160])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(meta_table)
        elements.append(Spacer(1, 14))

        # 4. Multi-Signal Score Breakdown
        elements.append(
            Paragraph("<b>Multi-Modal Verification Signals</b>", self.styles["Heading2"])
        )
        scores = result.decision.signal_scores
        online_score = scores.get("online_verification", 0.0)
        field_score = scores.get("field_matching", 0.0)
        integrity_score = scores.get("document_integrity", 0.0)

        sig_data = [
            ["Signal Component", "Weight", "Score", "Status"],
            [
                "Online Verification",
                "25%",
                f"{online_score * 100:.1f}%",
                "Verified" if online_score >= 0.8 else "Pending / Failed",
            ],
            [
                "Field Cross-Matching",
                "25%",
                f"{field_score * 100:.1f}%",
                "Aligned" if field_score >= 0.8 else "Mismatch / Inconclusive",
            ],
            [
                "Document Integrity (ELA & Noise)",
                "20%",
                f"{integrity_score * 100:.1f}%",
                "Clean" if integrity_score >= 0.7 else "Tampering Detected",
            ],
            [
                "QR Code Validation",
                "15%",
                f"{scores.get('qr_verification', 0.0) * 100:.1f}%",
                "Valid QR" if scores.get("qr_verification", 0.0) >= 0.8 else "Invalid / Absent",
            ],
            [
                "Issuer Domain Trust",
                "10%",
                f"{scores.get('domain_trust', 0.0) * 100:.1f}%",
                "Authoritative" if scores.get("domain_trust", 0.0) >= 0.8 else "Unverified Domain",
            ],
            [
                "Signature & Seal Forensics",
                "5%",
                f"{scores.get('signature_seal', 0.0) * 100:.1f}%",
                "Consistent" if scores.get("signature_seal", 0.0) >= 0.6 else "Flagged",
            ],
        ]
        sig_table = Table(sig_data, colWidths=[180, 70, 90, 180])
        sig_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_INDIGO),
                    ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                    ("TOPPADDING", (0, 0), (-1, 0), 5),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("PADDING", (0, 1), (-1, -1), 5),
                ]
            )
        )
        elements.append(sig_table)
        elements.append(Spacer(1, 14))

        # 5. Explanatory Findings & Risk Factors
        elements.append(
            Paragraph("<b>Decision Rationale & Audit Findings</b>", self.styles["Heading2"])
        )
        reasons_text = "<br/>".join([f"• {r}" for r in result.decision.decision_reasons])
        elements.append(
            Paragraph(
                reasons_text or "• All verification checks passed nominal baselines.",
                self.styles["Normal"],
            )
        )

        if result.decision.risk_factors:
            elements.append(Spacer(1, 8))
            elements.append(Paragraph("<b>Flagged Risk Factors:</b>", self.styles["Heading3"]))
            risks_text = "<br/>".join(
                [f"<font color='#B91C1C'>▲ {rf}</font>" for rf in result.decision.risk_factors]
            )
            elements.append(Paragraph(risks_text, self.styles["Normal"]))

        # Build Document
        doc.build(elements, canvasmaker=NumberedCanvas)

        if output_path:
            return output_path.read_bytes()
        return buffer.getvalue()
