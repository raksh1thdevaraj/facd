"""CLI tool to generate, digitally sign, and render official verification reports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.modules.report_generator.service import ReportService
from app.modules.score_fusion.service import ScoreFusionService
from app.schemas.pipeline import CertificateFields
from app.schemas.report import FileMetadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile, sign, and render verification reports (PDF & JSON)."
    )
    parser.add_argument(
        "--certificate-id", type=str, default="cert_sample_001", help="Certificate ID"
    )
    parser.add_argument(
        "--output-dir", type=str, default="storage/reports", help="Output directory for reports"
    )
    parser.add_argument(
        "--student-name", type=str, default="Jane Doe", help="Candidate Student Name"
    )
    parser.add_argument(
        "--roll-number", type=str, default="REG-2024-9981", help="Student Registration Number"
    )
    parser.add_argument(
        "--institution", type=str, default="National Institute of Technology", help="Institution"
    )
    args = parser.parse_args()

    print(f"Generating verification report for {args.certificate_id}...")

    fusion_service = ScoreFusionService()
    decision = fusion_service.fuse_and_decide(
        certificate_id=args.certificate_id,
        visual_fake_prob=0.08,
        tabular_fake_prob=0.05,
        forensic_score=0.92,
        text_consistency_score=0.96,
        template_score=0.95,
        tier_status="TIER_1_VERIFIED",
    )

    fields = CertificateFields(
        student_name=args.student_name,
        register_number=args.roll_number,
        institution_name=args.institution,
        course_degree="Bachelor of Technology in Computer Science",
        grade_or_marks="First Class with Distinction (CGPA 9.2)",
        issue_date="2024-05-20",
        certificate_number="NIT-CS-2024-0412",
    )

    file_meta = FileMetadata(
        filename=f"{args.certificate_id}.png",
        file_size_kb=342.5,
        file_format="PNG",
        sha256_checksum="4a5b6c7d8e9f0123456789abcdef0123456789abcdef0123456789abcdef0123",
    )

    service = ReportService(output_dir=Path(args.output_dir))
    report = service.generate_report(
        certificate_id=args.certificate_id,
        decision=decision,
        file_metadata=file_meta,
        extracted_fields=fields,
    )

    print("Report Generated Successfully!")
    print(f"  Report ID:     {report.report_id}")
    print(f"  Verdict:       {report.verdict.value}")
    print(f"  Authenticity:  {report.authenticity_percentage:.1f}%")
    print(f"  PDF Output:    {report.pdf_path}")
    print(f"  JSON Output:   {report.json_path}")
    print(f"  QR Code:       {report.qr_code_path}")
    print(f"  HMAC Digest:   {report.report_hmac_signature[:32]}...")


if __name__ == "__main__":
    main()
