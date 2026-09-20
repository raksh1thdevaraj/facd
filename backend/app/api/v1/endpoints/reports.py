"""FastAPI router for verification report retrieval, verification, and PDF/JSON downloads."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.report_generator.service import ReportService
from app.schemas.report import FullVerificationReport

router = APIRouter(prefix="/reports", tags=["Verification Reports"])


@router.get(
    "/{report_id}",
    response_model=FullVerificationReport,
    summary="Get Full Verification Report",
    description="Retrieve the complete verification report dossier in structured JSON format.",
)
def get_report_endpoint(
    report_id: str,
    db: Session = Depends(get_db),
) -> FullVerificationReport:
    service = ReportService()
    report = service.get_report(report_id, db=db)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification report with ID '{report_id}' not found.",
        )
    return report


@router.get(
    "/{report_id}/json",
    summary="Download Verification Report JSON",
    description="Download the machine-readable JSON report document.",
)
def download_json_endpoint(
    report_id: str,
    db: Session = Depends(get_db),
) -> JSONResponse:
    service = ReportService()
    report = service.get_report(report_id, db=db)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification report with ID '{report_id}' not found.",
        )
    headers = {"Content-Disposition": f"attachment; filename=verification_report_{report_id}.json"}
    return JSONResponse(content=report.model_dump(mode="json"), headers=headers)


@router.get(
    "/{report_id}/pdf",
    summary="Download Official Verification Report PDF",
    description="Download the official publication-grade verification report PDF.",
)
def download_pdf_endpoint(
    report_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    service = ReportService()
    pdf_path = service.get_pdf_path(report_id)

    if pdf_path is None or not pdf_path.exists():
        # Check if report exists in db/json to render it on the fly
        report = service.get_report(report_id, db=db)
        if report is not None:
            from app.modules.report_generator.pdf_renderer import PDFReportRenderer

            pdf_path = service.output_dir / f"{report_id}.pdf"
            PDFReportRenderer.render(report, pdf_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verification report PDF with ID '{report_id}' not found.",
            )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"verification_report_{report_id}.pdf",
    )


@router.get(
    "/{report_id}/verify",
    summary="Verify Report Digital Signature",
    description="Check whether report data has been altered by validating HMAC-SHA256 signature.",
)
def verify_report_integrity_endpoint(
    report_id: str,
    db: Session = Depends(get_db),
) -> dict:
    service = ReportService()
    report = service.get_report(report_id, db=db)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification report with ID '{report_id}' not found.",
        )

    is_valid = service.verify_authenticity(report)
    return {
        "report_id": report.report_id,
        "certificate_id": report.certificate_id,
        "is_authentic_and_unaltered": is_valid,
        "verdict": report.verdict.value,
        "authenticity_score": report.authenticity_score,
        "generated_at": report.generated_at.isoformat(),
    }
