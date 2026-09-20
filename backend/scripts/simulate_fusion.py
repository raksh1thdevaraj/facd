#!/usr/bin/env python3
"""CLI utility to simulate multimodal score fusion and inspect veto overrides."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add backend and root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.modules.score_fusion.service import ScoreFusionService
from app.schemas.template_matching import TierStatus


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate multimodal score fusion, institutional vetoes, and verdicts."
    )
    parser.add_argument(
        "--visual-fake-prob",
        type=float,
        default=0.20,
        help="Visual CNN fake probability [0.0, 1.0]",
    )
    parser.add_argument(
        "--tabular-fake-prob",
        type=float,
        default=0.15,
        help="Tabular ML fake probability [0.0, 1.0]",
    )
    parser.add_argument(
        "--forensic-score", type=float, default=0.85, help="Forensic integrity score [0.0, 1.0]"
    )
    parser.add_argument(
        "--text-consistency-score",
        type=float,
        default=0.90,
        help="Text consistency score [0.0, 1.0]",
    )
    parser.add_argument(
        "--template-score", type=float, default=0.88, help="Template match score [0.0, 1.0]"
    )
    parser.add_argument(
        "--tier",
        type=str,
        default="TIER_3_UNVERIFIED",
        choices=[
            "TIER_1_VERIFIED",
            "TIER_2_CONSISTENT",
            "TIER_3_INCONSISTENT",
            "TIER_3_UNVERIFIED",
        ],
        help="Database record verification tier",
    )
    parser.add_argument(
        "--record-found", action="store_true", help="Set if student record was found in database"
    )
    parser.add_argument(
        "--discrepancy", type=str, default=None, help="Discrepancy description if any"
    )
    parser.add_argument(
        "--fusion-method",
        type=str,
        default="late_fusion",
        choices=["late_fusion", "stacking_meta_learner"],
        help="Fusion strategy to employ",
    )
    parser.add_argument("--json-output", type=str, default=None, help="Path to write JSON results")

    args = parser.parse_args()

    service = ScoreFusionService(default_fusion_method=args.fusion_method)
    discrepancies = [args.discrepancy] if args.discrepancy else None

    decision = service.fuse_and_decide(
        certificate_id="SIMULATED_DOC",
        visual_fake_prob=args.visual_fake_prob,
        tabular_fake_prob=args.tabular_fake_prob,
        forensic_score=args.forensic_score,
        text_consistency_score=args.text_consistency_score,
        template_score=args.template_score,
        tier_status=TierStatus(args.tier),
        record_found=args.record_found,
        discrepancies=discrepancies,
        fusion_method=args.fusion_method,
    )

    print("\n" + "=" * 55)
    print("MULTIMODAL SCORE FUSION SIMULATION RESULT")
    print("=" * 55)
    print(f"Verdict:                    {decision.verdict.value}")
    print(f"Risk Band:                  {decision.risk_band.value}")
    print(f"Overall Authenticity Score: {decision.overall_authenticity_score * 100:.2f}%")
    print(f"Overall Risk Score:         {decision.overall_risk_score:.2f} / 100")
    print(f"Confidence Level:           {decision.confidence * 100:.1f}%")
    print(f"Institutional Tier:         {decision.tier_status}")
    print(f"Veto Applied:               {decision.veto_applied}")
    if decision.veto_reason:
        print(f"Veto Reason:                {decision.veto_reason}")
    print(f"Fusion Method:              {decision.fusion_method}")
    print("-" * 55)
    print("SUB-SCORES BREAKDOWN:")
    print(f"  • Visual Branch:          {decision.sub_scores.visual_branch_score * 100:.1f}%")
    print(f"  • Tabular ML Branch:      {decision.sub_scores.tabular_branch_score * 100:.1f}%")
    print(f"  • Forensic Integrity:     {decision.sub_scores.forensic_score * 100:.1f}%")
    print(f"  • Text Consistency:       {decision.sub_scores.text_consistency_score * 100:.1f}%")
    print(f"  • Template Match:         {decision.sub_scores.template_score * 100:.1f}%")
    print("-" * 55)
    print(f"Summary Rationale:\n  {decision.summary_rationale}")
    print("=" * 55 + "\n")

    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(decision.model_dump(), f, indent=2)
        print(f"Simulated decision saved to {args.json_output}")


if __name__ == "__main__":
    main()
