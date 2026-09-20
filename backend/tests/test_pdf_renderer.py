"""Unit tests for ReportLab PDF compilation and rendering performance (TC-REP-02)."""

import time
from pathlib import Path

from PIL import Image

from app.modules.report_generator.assembler import ReportAssembler
from app.modules.report_generator.pdf_renderer import PDFReportRenderer
from app.modules.report_generator.qr_generator import generate_report_qr
from app.modules.score_fusion.service import ScoreFusionService
from app.schemas.explainability import FindingBullet, FindingCategory, FindingSeverity
from app.schemas.pipeline import CertificateFields
from app.schemas.report import VisualEvidencePaths


def test_pdf_renderer_generates_valid_pdf(tmp_path: Path):
    """Verify PDF compiles with header, banner, tables, images, and QR (TC-REP-02)."""
    fusion = ScoreFusionService()
    decision = fusion.fuse_and_decide(
        certificate_id="cert-pdf-001",
        visual_fake_prob=0.1,
        tabular_fake_prob=0.1,
        forensic_score=0.9,
        text_consistency_score=0.9,
        template_score=0.9,
    )

    # Create dummy images for evidence plates
    img_orig = tmp_path / "orig.png"
    img_over = tmp_path / "overlay.png"
    Image.new("RGB", (600, 400), color=(240, 240, 240)).save(img_orig)
    Image.new("RGB", (600, 400), color=(200, 220, 240)).save(img_over)

    qr_path = generate_report_qr("rep-pdf-001", output_dir=tmp_path)

    report = ReportAssembler.assemble(
        certificate_id="cert-pdf-001",
        decision=decision,
        extracted_fields=CertificateFields(
            student_name="Bob Jones",
            register_number="REG-BOB-42",
            institution_name="Tech University",
            course_degree="B.S. Information Systems",
            grade_or_marks="First Class",
            issue_date="2023-11-10",
        ),
        visual_evidence=VisualEvidencePaths(
            original_image=str(img_orig),
            unified_overlay=str(img_over),
        ),
    )
    report.qr_code_path = str(qr_path)
    report.report_hmac_signature = "a" * 64
    report.findings = [
        FindingBullet(
            id="f1",
            severity=FindingSeverity.INFO,
            category=FindingCategory.DATABASE_RECORD,
            title="Database Record Match",
            description="All registrar details match official university archive.",
        )
    ]

    out_pdf = tmp_path / "test_report.pdf"

    t0 = time.perf_counter()
    res_path = PDFReportRenderer.render(report, out_pdf)
    elapsed = time.perf_counter() - t0

    assert res_path.exists()
    assert res_path.is_file()
    assert res_path.stat().st_size > 1000  # Non-trivial PDF size
    assert elapsed < 3.0  # NFR-03 requirement

    # Validate PDF Magic Bytes
    with open(res_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"


def test_pdf_renderer_handles_missing_evidence_gracefully(tmp_path: Path):
    """Verify PDF renderer succeeds even when evidence plates are absent."""
    fusion = ScoreFusionService()
    decision = fusion.fuse_and_decide(
        certificate_id="cert-pdf-missing",
        visual_fake_prob=0.8,
        tabular_fake_prob=0.8,
        forensic_score=0.4,
        text_consistency_score=0.4,
        template_score=0.3,
    )

    report = ReportAssembler.assemble(
        certificate_id="cert-pdf-missing",
        decision=decision,
        visual_evidence=VisualEvidencePaths(
            original_image="/nonexistent/path/orig.png",
            unified_overlay=None,
        ),
    )

    out_pdf = tmp_path / "missing_evidence_report.pdf"
    res_path = PDFReportRenderer.render(report, out_pdf)

    assert res_path.exists()
    assert res_path.stat().st_size > 1000
