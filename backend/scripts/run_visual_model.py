#!/usr/bin/env python3
"""CLI utility to execute deep learning visual model and Grad-CAM on a certificate image."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add backend and root directory to sys.path so app imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.modules.visual_model.service import VisualCNNService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deep learning visual CNN tampering classification and Grad-CAM."
    )
    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path to the input certificate image (JPG/PNG).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="ml/models/visual_cnn_best.pt",
        help="Optional path to model checkpoint.",
    )
    parser.add_argument(
        "--output-gradcam",
        type=str,
        default=None,
        help="Optional path to save generated Grad-CAM overlay image.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device to use (cpu, mps, or cuda).",
    )
    parser.add_argument(
        "--json-output",
        type=str,
        default=None,
        help="Optional path to write JSON prediction results.",
    )

    args = parser.parse_args()
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: Image not found at {image_path}", file=sys.stderr)
        sys.exit(1)

    model_path = Path(args.model) if Path(args.model).exists() else None
    service = VisualCNNService(model_path=model_path, device=args.device)

    out_dir = Path(args.output_gradcam).parent if args.output_gradcam else None
    result = service.predict(
        image_path=image_path,
        generate_gradcam=True,
        output_dir=out_dir,
    )

    if args.output_gradcam and result.gradcam_heatmap_path:
        # Move or rename if specific path was given
        dest = Path(args.output_gradcam)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if str(dest) != result.gradcam_heatmap_path:
            import shutil

            shutil.copyfile(result.gradcam_heatmap_path, dest)
            result.gradcam_heatmap_path = str(dest)

    print("\n" + "=" * 50)
    print("CERTIFICATE VISUAL CNN TAMPERING PREDICTION")
    print("=" * 50)
    print(f"Image:                     {image_path.name}")
    print(f"Predicted Class:           {result.predicted_class.upper()}")
    print(f"Manipulation Probability:  {result.manipulation_probability:.4f}")
    print(f"Confidence:                {result.confidence:.4f}")
    print(f"Visual Embedding Dim:      {len(result.visual_embedding)}")
    print(f"Grad-CAM Heatmap:          {result.gradcam_heatmap_path or 'N/A'}")
    print(f"Inference Latency:         {result.latency_ms:.2f} ms")
    print("=" * 50)

    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2)
        print(f"JSON results saved to {args.json_output}")


if __name__ == "__main__":
    main()
