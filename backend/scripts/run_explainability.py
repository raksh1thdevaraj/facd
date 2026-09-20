#!/usr/bin/env python3
"""CLI utility to generate explainability reports and visual evidence dossiers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

# Add backend and root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.modules.explainability.service import ExplainabilityService
from app.modules.score_fusion.service import ScoreFusionService


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate natural language explanations, SHAP attributions, "
            "and visual evidence overlay."
        )
    )
    parser.add_argument(
        "--image", type=str, required=True, help="Path to certificate image (PNG/JPG)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="storage/reports", help="Directory for reports"
    )
    parser.add_argument(
        "--json-output", type=str, default=None, help="Path to save output JSON report"
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: Certificate image not found at {image_path}", file=sys.stderr)
        sys.exit(1)

    # 1. Synthesize baseline decision for simulation
    fusion_svc = ScoreFusionService()
    decision = fusion_svc.fuse_and_decide(
        certificate_id=image_path.stem,
        visual_fake_prob=0.25,
        tabular_fake_prob=0.15,
        forensic_score=0.88,
        text_consistency_score=0.92,
        template_score=0.90,
    )

    # 2. Run Explainability Service
    exp_svc = ExplainabilityService()
    dummy_feats = np.array([1200.0, 1.0, 0.0, 0.05] + [0.9] * 18, dtype=np.float32)

    report = exp_svc.explain_certificate(
        certificate_id=image_path.stem,
        raw_image_path=image_path,
        decision=decision,
        tabular_features=dummy_feats,
        output_dir=args.output_dir,
    )

    print("\n" + "=" * 60)
    print("EXPLAINABILITY & EVIDENCE DOSSIER")
    print("=" * 60)
    print(f"Certificate:               {image_path.name}")
    print(f"Overall Verdict:           {decision.verdict.value} ({decision.risk_band.value} RISK)")
    print(f"Authenticity Score:        {decision.overall_authenticity_score * 100:.1f}%")
    print("-" * 60)
    print("EXECUTIVE SUMMARY:")
    print(f"  {report.primary_verdict_rationale}")
    print("-" * 60)
    print("KEY FINDINGS:")
    for f in report.key_findings:
        print(f"  [{f.severity.value}] {f.title}: {f.description}")
    print("-" * 60)
    print("TOP SHAP FEATURE ATTRIBUTIONS:")
    for attr in report.top_contributing_features:
        sign = "+" if attr.direction == "INCREASES_RISK" else "-"
        print(f"  • {attr.feature_name:<28} {sign}{attr.impact_percentage:.1f}% ({attr.direction})")
    print("-" * 60)
    print(f"Visual Evidence Overlay:   {report.unified_overlay_path or 'N/A'}")
    print(f"Execution Latency:         {report.execution_time_ms:.2f} ms")
    print("=" * 60 + "\n")

    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)
        print(f"Explainability report saved to {args.json_output}")


if __name__ == "__main__":
    main()
