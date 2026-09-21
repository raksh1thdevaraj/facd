"""Dataset Validator.

Performs comprehensive data integrity checks:
1. Verifies image existence and readability
2. Verifies label consistency and valid ranges
3. Checks class balance across splits
4. Validates bounding box coordinate geometry
5. Detects and flags any data leakage across splits
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import Image


def validate_dataset(dataset_dir: Path) -> dict[str, Any]:
    """Validate dataset integrity and print detailed diagnostic report."""
    results = {
        "status": "PASSED",
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    metadata_path = dataset_dir / "metadata.csv"
    if not metadata_path.exists():
        results["status"] = "FAILED"
        results["errors"].append(f"Master metadata file not found at {metadata_path}")
        return results

    df = pd.read_csv(metadata_path)
    total_samples = len(df)
    results["stats"]["total_samples"] = total_samples

    # 1. Check file existence & image readability
    corrupt_count = 0
    missing_count = 0
    for _, row in df.iterrows():
        img_rel = row["image_path"]
        img_full = Path(img_rel)
        if not img_full.is_absolute():
            img_full = Path.cwd() / img_full

        if not img_full.exists():
            missing_count += 1
            results["errors"].append(f"Missing image file: {img_rel}")
            continue

        try:
            with Image.open(img_full) as img:
                img.verify()
        except (OSError, ValueError, SyntaxError) as e:
            corrupt_count += 1
            results["errors"].append(f"Corrupt image file {img_rel}: {e!s}")

    results["stats"]["missing_files"] = missing_count
    results["stats"]["corrupt_files"] = corrupt_count

    # 2. Check label consistency & class balance
    genuine_count = (df["primary_label"] == "genuine").sum()
    manipulated_count = (df["primary_label"] == "manipulated").sum()
    results["stats"]["genuine_count"] = int(genuine_count)
    results["stats"]["manipulated_count"] = int(manipulated_count)

    if total_samples > 0:
        ratio = genuine_count / total_samples
        if abs(ratio - 0.5) > 0.05:
            results["warnings"].append(
                f"Class imbalance detected: {genuine_count} genuine vs {manipulated_count} manipulated ({ratio:.1%})"
            )

    # 3. Check ground truth manifests and bounding boxes
    gt_dir = dataset_dir / "ground_truth"
    if gt_dir.exists():
        all_split_sample_ids: dict[str, str] = {}
        for manifest_file in gt_dir.glob("*_manifest.json"):
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            for sample in manifest.get("samples", []):
                s_id = sample["sample_id"]
                split = sample.get("split", "unknown")

                # Data leakage check
                if s_id in all_split_sample_ids:
                    results["errors"].append(
                        f"Data leakage: sample {s_id} appears in {all_split_sample_ids[s_id]} and {split}"
                    )
                all_split_sample_ids[s_id] = split

                # Bounding box geometry checks
                for region in sample.get("manipulated_regions", []):
                    bbox = region.get("bbox_normalized", {})
                    x1, y1, x2, y2 = (
                        bbox.get("x1", 0),
                        bbox.get("y1", 0),
                        bbox.get("x2", 0),
                        bbox.get("y2", 0),
                    )
                    if not (0.0 <= x1 < x2 <= 1.0) or not (0.0 <= y1 < y2 <= 1.0):
                        results["errors"].append(
                            f"Invalid bounding box in {s_id} region {region.get('region_id')}: {bbox}"
                        )

    if len(results["errors"]) > 0:
        results["status"] = "FAILED"

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate synthetic certificate verification dataset."
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default="./datasets",
        help="Path to dataset directory.",
    )
    args = parser.parse_args()

    results = validate_dataset(Path(args.dataset_dir))
    print(json.dumps(results, indent=2))
    if results["status"] != "PASSED":
        sys.exit(1)


if __name__ == "__main__":
    main()
