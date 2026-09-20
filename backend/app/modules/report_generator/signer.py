"""Cryptographic HMAC-SHA256 digital signature generator and tamper verification."""

from __future__ import annotations

import hashlib
import hmac

from app.schemas.report import FullVerificationReport


def construct_canonical_string(report_data: FullVerificationReport) -> str:
    """Construct a canonical deterministic string representing core report data."""
    register_num = report_data.extracted_fields.register_number or ""
    verdict_str = (
        report_data.verdict.value
        if hasattr(report_data.verdict, "value")
        else str(report_data.verdict)
    )
    return (
        f"{report_data.report_id}|"
        f"{report_data.certificate_id}|"
        f"{report_data.file_metadata.sha256_checksum}|"
        f"{verdict_str}|"
        f"{report_data.authenticity_score:.4f}|"
        f"{register_num}|"
        f"{report_data.generated_at.isoformat()}"
    )


def sign_report(report_data: FullVerificationReport, secret_key: str) -> str:
    """Compute HMAC-SHA256 digital signature across canonical report data."""
    canonical = construct_canonical_string(report_data)
    return hmac.new(
        secret_key.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_report_signature(
    report_data: FullVerificationReport, signature: str, secret_key: str
) -> bool:
    """Verify digital signature using constant-time comparison."""
    if not signature:
        return False
    expected = sign_report(report_data, secret_key)
    return hmac.compare_digest(expected, signature)
