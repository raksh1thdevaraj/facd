"""Verification QR code generator linking physical reports to digital records."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import qrcode


def generate_report_qr(
    report_id: str,
    base_url: str = "http://localhost:8000",
    output_dir: Optional[Path] = None,
) -> Path:
    """Generate a high-contrast scannable QR code encoding the verification URL.

    Args:
        report_id: Unique UUID string of the verification report.
        base_url: Base domain and protocol of the verification service.
        output_dir: Directory where the QR code PNG image will be saved.

    Returns:
        Path to the generated PNG QR image.
    """
    if output_dir is None:
        output_dir = Path("storage/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    verification_url = f"{base_url.rstrip('/')}/verify-report/{report_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    output_path = output_dir / f"{report_id}_qr.png"
    img.save(str(output_path))

    return output_path
