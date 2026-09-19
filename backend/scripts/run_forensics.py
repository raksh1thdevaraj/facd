#!/usr/bin/env python3
"""CLI utility to execute Error Level Analysis, Copy-Move detection, and Noise Analysis
on any certificate image and save standalone visual heatmaps and JSON reports.
"""

import argparse
import json
import sys
from pathlib import Path

# Add backend directory to sys.path so app imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.modules.forensics.service import ForensicService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run classical digital image forensics on a certificate image."
    )
    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to the input certificate image (JPG/PNG).",
    )
    parser.add_argument(
        "--output-heatmap",
        type=str,
        default=None,
        help="Optional path to save the generated composite thermal heatmap PNG.",
    )
    parser.add_argument(
        "--json-output",
        type=str,
        default=None,
        help="Optional path to write the JSON results.",
    )

    args = parser.parse_args()
    image_path = Path(args.image)

    if not image_path.exists():
        print(f"Error: image file not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    heatmap_path = Path(args.output_heatmap) if args.output_heatmap else None

    service = ForensicService()
    print(f"[*] Analyzing forensics on: {image_path}...")
    result = service.analyze(
        document_id=image_path.stem,
        raw_image_or_path=image_path,
        output_heatmap_path=heatmap_path,
    )

    summary = {
        "document_id": result.document_id,
        "overall_forensic_score": result.overall_forensic_score,
        "ela_score": result.ela_score,
        "copy_move_score": result.copy_move_score,
        "noise_inconsistency_score": result.noise_inconsistency_score,
        "forensics_risk_score": result.forensics_risk_score,
        "detected_clones_count": len(result.detected_clones),
        "suspicious_regions_count": len(result.suspicious_regions),
        "heatmap_image_path": result.heatmap_image_path,
        "execution_time_ms": result.execution_time_ms,
    }

    print("\n=== Forensic Analysis Findings ===")
    print(json.dumps(summary, indent=2))

    if args.json_output:
        out_file = Path(args.json_output)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"[+] JSON report saved to: {out_file}")

    if result.heatmap_image_path:
        print(f"[+] Thermal heatmap generated: {result.heatmap_image_path}")


if __name__ == "__main__":
    main()
