"""ReportLab PDF document compiler and visual evidence section renderer."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

from PIL import Image as PILImage
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
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
from app.schemas.decision import VerificationVerdict
from app.schemas.report import FullVerificationReport


def _fit_image(
    image_path: Optional[str], max_w: float = 240.0, max_h: float = 160.0
) -> Optional[Image]:
    """Load image from path and scale proportionally to fit within max bounds."""
    if not image_path:
        return None
    p = Path(image_path)
    if not p.exists() or not p.is_file():
        return None

    try:
        with PILImage.open(p) as pil_img:
            orig_w, orig_h = pil_img.size
            if orig_w <= 0 or orig_h <= 0:
                return None
            scale = min(max_w / orig_w, max_h / orig_h, 1.0)
            target_w = orig_w * scale
            target_h = orig_h * scale
            return Image(str(p), width=target_w, height=target_h)
    except Exception:
        return None


class PDFReportRenderer:
    """Compiles FullVerificationReport into a publication-grade multi-page PDF."""

    @classmethod
    def render(cls, report_data: FullVerificationReport, output_path: Path) -> Path:
        """Build and save PDF report to destination path.

        Args:
            report_data: Comprehensive verification report data model.
            output_path: Target filesystem path for the PDF binary.

        Returns:
            Path to the compiled PDF file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=42,
        )

        story = cls.build_story(report_data)
        doc.build(story, canvasmaker=NumberedCanvas)
        return output_path

    @classmethod
    def build_story(cls, report_data: FullVerificationReport) -> List[Any]:
        """Construct the flowable story sequence for ReportLab."""
        styles = get_report_styles()
        story: List[Any] = []

        # =========================================================================
        # 1. Header & Document Title
        # =========================================================================
        story.append(Paragraph("ACADEMIC CREDENTIAL VERIFICATION DOSSIER", styles["ReportTitle"]))
        dt_str = report_data.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        sub_text = (
            f"Report ID: <b>{report_data.report_id}</b> &nbsp;|&nbsp; "
            f"Date: <b>{dt_str}</b> &nbsp;|&nbsp; "
            f"Auditor: <b>{report_data.verifier_username}</b>"
        )
        story.append(Paragraph(sub_text, styles["ReportSubtitle"]))
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_NAVY, spaceAfter=8))

        # =========================================================================
        # 2. Executive Verdict Banner
        # =========================================================================
        v_val = report_data.verdict
        if v_val == VerificationVerdict.AUTHENTIC:
            bg_col = COLOR_AUTHENTIC_BG
            fg_col = COLOR_AUTHENTIC_FG
            status_text = "VERIFIED AUTHENTIC"
        elif v_val == VerificationVerdict.SUSPICIOUS:
            bg_col = COLOR_SUSPICIOUS_BG
            fg_col = COLOR_SUSPICIOUS_FG
            status_text = "SUSPICIOUS — MANUAL REVIEW REQUIRED"
        else:
            bg_col = COLOR_MANIPULATED_BG
            fg_col = COLOR_MANIPULATED_FG
            status_text = "DIGITALLY MANIPULATED / FRAUD DETECTED"

        banner_title = (
            f"<font color='{fg_col.hexval()}'><b>VERDICT: {status_text}</b></font><br/>"
            f"<font size=8 color='#424242'>Authenticity: "
            f"<b>{report_data.authenticity_percentage:.1f}%</b> &nbsp;|&nbsp; "
            f"Risk: <b>{report_data.risk_score:.1f}/100 ({report_data.risk_band.value})</b> "
            f"&nbsp;|&nbsp; Confidence: <b>{report_data.confidence_score * 100:.1f}%</b> "
            f"&nbsp;|&nbsp; Tier: <b>{report_data.tier_status}</b></font>"
        )

        verdict_cells = [
            [Paragraph(banner_title, styles["VerdictHeading"])],
            [Paragraph(report_data.executive_summary, styles["VerdictParagraph"])],
        ]
        if report_data.veto_applied and report_data.veto_reason:
            veto_text = (
                f"<font color='{COLOR_MANIPULATED_FG.hexval()}'><b>Institutional Override:</b> "
                f"{report_data.veto_reason}</font>"
            )
            verdict_cells.append([Paragraph(veto_text, styles["VerdictParagraph"])])

        verdict_table = Table(verdict_cells, colWidths=[523])
        verdict_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), bg_col),
                    ("BOX", (0, 0), (-1, -1), 1.2, fg_col),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(verdict_table)
        story.append(Spacer(1, 10))

        # =========================================================================
        # 3. Extracted Academic Credentials Grid
        # =========================================================================
        story.append(Paragraph("1. EXTRACTED ACADEMIC CREDENTIALS", styles["SectionHeader"]))
        f = report_data.extracted_fields

        cred_data = [
            [
                Paragraph("Student Name", styles["FieldLabel"]),
                Paragraph(f.student_name or "Not Extracted", styles["FieldValue"]),
                Paragraph("Registration / Roll No.", styles["FieldLabel"]),
                Paragraph(f.register_number or "Not Extracted", styles["FieldValue"]),
            ],
            [
                Paragraph("Degree / Program", styles["FieldLabel"]),
                Paragraph(f.course_degree or "Not Extracted", styles["FieldValue"]),
                Paragraph("Issuing Institution", styles["FieldLabel"]),
                Paragraph(f.institution_name or "Not Extracted", styles["FieldValue"]),
            ],
            [
                Paragraph("Issue Date", styles["FieldLabel"]),
                Paragraph(f.issue_date or "Not Extracted", styles["FieldValue"]),
                Paragraph("Grade / CGPA / Marks", styles["FieldLabel"]),
                Paragraph(f.grade_or_marks or "Not Extracted", styles["FieldValue"]),
            ],
            [
                Paragraph("Certificate Serial", styles["FieldLabel"]),
                Paragraph(f.certificate_number or "Not Extracted", styles["FieldValue"]),
                Paragraph("File SHA-256 Digest", styles["FieldLabel"]),
                Paragraph(
                    report_data.file_metadata.sha256_checksum[:20] + "...",
                    styles["FieldValue"],
                ),
            ],
        ]

        cred_table = Table(cred_data, colWidths=[100, 161, 120, 142])
        cred_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(cred_table)
        story.append(Spacer(1, 10))

        # =========================================================================
        # 4. Analytical Subsystem Scores Table
        # =========================================================================
        story.append(Paragraph("2. ANALYTICAL SUBSYSTEM SCORE BREAKDOWN", styles["SectionHeader"]))

        score_rows = [
            [
                Paragraph("Analytical Subsystem", styles["TableHead"]),
                Paragraph("Score", styles["TableHead"]),
                Paragraph("Weight", styles["TableHead"]),
                Paragraph("Status", styles["TableHead"]),
                Paragraph("Technical Findings Summary", styles["TableHead"]),
            ]
        ]

        for sub in report_data.subsystem_scores:
            status_color = (
                COLOR_AUTHENTIC_FG
                if sub.status.upper() in ("PASSED", "VERIFIED", "GENUINE")
                else (
                    COLOR_SUSPICIOUS_FG
                    if sub.status.upper() in ("WARNING", "BORDERLINE")
                    else COLOR_MANIPULATED_FG
                )
            )
            score_rows.append(
                [
                    Paragraph(sub.name, styles["TableCell"]),
                    Paragraph(f"{sub.score:.2f}", styles["TableCell"]),
                    Paragraph(f"{sub.weight * 100:.0f}%", styles["TableCell"]),
                    Paragraph(
                        f"<font color='{status_color.hexval()}'><b>{sub.status}</b></font>",
                        styles["TableCell"],
                    ),
                    Paragraph(sub.detail, styles["TableCell"]),
                ]
            )

        if len(score_rows) == 1:
            # Fallback row if no subscores given
            score_rows.append(
                [
                    Paragraph("Multimodal Ensemble Fusion", styles["TableCell"]),
                    Paragraph(f"{report_data.authenticity_score:.2f}", styles["TableCell"]),
                    Paragraph("100%", styles["TableCell"]),
                    Paragraph("EVALUATED", styles["TableCell"]),
                    Paragraph(f"Verdict: {report_data.verdict.value}", styles["TableCell"]),
                ]
            )

        sub_table = Table(score_rows, colWidths=[130, 45, 45, 75, 228])
        sub_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#E8EAF6")),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(sub_table)
        story.append(Spacer(1, 10))

        # =========================================================================
        # 5. Key Categorized Findings Dossier
        # =========================================================================
        story.append(Paragraph("3. KEY INVESTIGATIVE FINDINGS", styles["SectionHeader"]))
        if report_data.findings:
            for item in report_data.findings[:6]:  # Show top findings
                sev = item.severity.value
                sev_color = (
                    COLOR_MANIPULATED_FG.hexval()
                    if sev == "CRITICAL"
                    else (
                        COLOR_SUSPICIOUS_FG.hexval()
                        if sev in ("MAJOR", "WARNING")
                        else COLOR_AUTHENTIC_FG.hexval()
                    )
                )
                bullet_text = (
                    f"• <font color='{sev_color}'><b>[{sev}] {item.title}:</b></font> "
                    f"{item.description}"
                )
                if item.evidence_value:
                    bullet_text += f" <i>(Evidence: {item.evidence_value})</i>"
                story.append(Paragraph(bullet_text, styles["BulletItem"]))
        else:
            story.append(
                Paragraph(
                    "• <font color='#1B5E20'><b>[INFO] No Anomalies Detected:</b></font> "
                    "Document conforms cleanly to authentic institutional standards.",
                    styles["BulletItem"],
                )
            )

        # =========================================================================
        # 6. Page Break to Page 2: Visual Evidence Annex
        # =========================================================================
        story.append(PageBreak())

        story.append(
            Paragraph("4. VISUAL EVIDENCE & FORENSIC PLATES ANNEX", styles["SectionHeader"])
        )
        story.append(
            Paragraph(
                "Side-by-side comparison of original document, multi-layer unified "
                "anomaly overlay, digital forensics recompression heatmap, and deep "
                "learning attention map.",
                styles["ReportSubtitle"],
            )
        )
        story.append(Spacer(1, 6))

        # 2x2 Plate Matrix
        p_orig = _fit_image(report_data.visual_evidence.original_image)
        p_over = _fit_image(report_data.visual_evidence.unified_overlay)
        p_foren = _fit_image(report_data.visual_evidence.forensic_heatmap)
        p_grad = _fit_image(report_data.visual_evidence.gradcam_heatmap)

        def make_plate_cell(img: Optional[Image], title: str) -> List[Any]:
            content: List[Any] = []
            if img:
                content.append(img)
            else:
                placeholder = Table(
                    [
                        [
                            Paragraph(
                                "<font color='#9E9E9E'>Plate Not Available</font>",
                                styles["TableCell"],
                            )
                        ]
                    ],
                    colWidths=[240],
                    rowHeights=[140],
                )
                placeholder.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ]
                    )
                )
                content.append(placeholder)
            content.append(Paragraph(title, styles["PlateCaption"]))
            return content

        plate_cells = [
            [
                make_plate_cell(p_orig, "Plate A: Original Uploaded Certificate"),
                make_plate_cell(p_over, "Plate B: Unified Anomaly Overlay & Bounding Boxes"),
            ],
            [
                make_plate_cell(p_foren, "Plate C: Digital Forensics & ELA Recompression"),
                make_plate_cell(p_grad, "Plate D: Visual AI Deep Learning Attention Map"),
            ],
        ]

        plates_table = Table(plate_cells, colWidths=[261, 261])
        plates_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(plates_table)
        story.append(Spacer(1, 8))

        # =========================================================================
        # 7. Verification QR Code, HMAC Signature & Legal Disclaimer
        # =========================================================================
        qr_img = _fit_image(report_data.qr_code_path, max_w=75.0, max_h=75.0)

        left_legal = [
            Paragraph(
                f"<b>Digital HMAC Signature:</b> <font face='Courier' size=6>"
                f"{report_data.report_hmac_signature or 'UNSIGNED'}</font>",
                styles["TableCell"],
            ),
            Spacer(1, 3),
            Paragraph(
                f"<b>Verification URL:</b> <font color='{COLOR_INDIGO.hexval()}'>"
                f"{report_data.verification_url or 'N/A'}</font>",
                styles["TableCell"],
            ),
            Spacer(1, 3),
            Paragraph(report_data.disclaimer, styles["LegalNotice"]),
        ]

        right_qr: List[Any] = []
        if qr_img:
            right_qr.append(qr_img)
        right_qr.append(
            Paragraph(
                "<font size=6.5>Scan to verify official report</font>",
                styles["PlateCaption"],
            )
        )

        footer_table = Table([[left_legal, right_qr]], colWidths=[420, 103])
        footer_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(KeepTogether([footer_table]))

        return story
