"""ReportLab stylesheet, typography, color palette, and dynamic numbered canvas."""

from __future__ import annotations

from typing import Any, Dict

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.pdfgen import canvas

# Color Palette
COLOR_NAVY = HexColor("#1A237E")
COLOR_INDIGO = HexColor("#283593")
COLOR_BORDER = HexColor("#E0E0E0")
COLOR_TEXT_MAIN = HexColor("#212121")
COLOR_TEXT_MUTED = HexColor("#616161")
COLOR_LIGHT_BG = HexColor("#F8F9FA")

# Verdict Colors
COLOR_AUTHENTIC_BG = HexColor("#E8F5E9")
COLOR_AUTHENTIC_FG = HexColor("#1B5E20")
COLOR_SUSPICIOUS_BG = HexColor("#FFF8E1")
COLOR_SUSPICIOUS_FG = HexColor("#F57F17")
COLOR_MANIPULATED_BG = HexColor("#FFEBEE")
COLOR_MANIPULATED_FG = HexColor("#B71C1C")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas recording total page count for 'Page X of Y' footers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[Dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int) -> None:
        """Draw standard running header and running footer."""
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(COLOR_INDIGO)

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 810, "ACADEMIC CERTIFICATE VERIFICATION DOSSIER — OFFICIAL AUDIT")
            self.setStrokeColor(COLOR_BORDER)
            self.setLineWidth(0.5)
            self.line(36, 804, 559, 804)

        # Running Footer
        self.setFont("Helvetica", 7.5)
        self.setFillColor(COLOR_TEXT_MUTED)
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(36, 38, 559, 38)

        self.drawString(
            36, 26, "Official Verification Dossier • AI Academic Certificate Integrity System"
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(559, 26, page_str)
        self.restoreState()


def get_report_styles() -> StyleSheet1:
    """Build standardized publication typography stylesheet."""
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=COLOR_NAVY,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_TEXT_MUTED,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeader",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=COLOR_INDIGO,
            spaceBefore=8,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="VerdictHeading",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=16,
            textColor=COLOR_NAVY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="VerdictParagraph",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=COLOR_TEXT_MAIN,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FieldLabel",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=COLOR_TEXT_MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FieldValue",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_TEXT_MAIN,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHead",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=COLOR_NAVY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=COLOR_TEXT_MAIN,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletItem",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=COLOR_TEXT_MAIN,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="PlateCaption",
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_INDIGO,
            alignment=1,  # Center
            spaceBefore=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="LegalNotice",
            fontName="Helvetica",
            fontSize=7,
            leading=8.5,
            textColor=COLOR_TEXT_MUTED,
        )
    )

    return styles
