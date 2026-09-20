"""JSON serializer and file exporter for machine-readable verification reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.schemas.report import FullVerificationReport


def export_json_report(
    report_data: FullVerificationReport, output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Serialize FullVerificationReport to standard JSON dict and optional file.

    Args:
        report_data: Verified report data model.
        output_path: Optional destination filesystem path.

    Returns:
        Serialized Python dictionary representation.
    """
    payload = report_data.model_dump(mode="json")

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    return payload
