"""Dataset Pipeline Orchestrator.

Orchestrates the entire certificate synthesis lifecycle:
1. Base template generation
2. Genuine certificate generation
3. Synthetic tampering injection
4. Master metadata annotation
5. Train/Val/Test partitioning & SPEC-04 manifest export
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd

from ml.scripts.generate_genuine import (
    generate_synthetic_record,
    render_genuine_certificate,
)
from ml.scripts.generate_manipulated import apply_manipulation
from ml.scripts.generate_templates import generate_all_templates
from ml.scripts.split_dataset import create_dataset_splits


def generate_dataset(
    sample_count: int = 200,
    output_base_dir: Path = Path("./datasets"),
    ml_data_dir: Path = Path("./ml/data"),
    seed: int = 42,
) -> dict[str, Any]:
    """Generate a balanced, labeled dataset of genuine and manipulated certificates."""
    random.seed(seed)

    output_base_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_base_dir / "raw"
    assets_dir = output_base_dir / "assets"
    synth_dir = output_base_dir / "synthetic_manipulated"
    genuine_dir = synth_dir / "genuine"
    manipulated_dir = synth_dir / "manipulated"

    genuine_dir.mkdir(parents=True, exist_ok=True)
    manipulated_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ensure base templates exist
    templates_meta_path = raw_dir / "templates_meta.json"
    if not templates_meta_path.exists():
        print("Generating base certificate templates...")
        templates = generate_all_templates(output_base_dir)
    else:
        with open(templates_meta_path, "r", encoding="utf-8") as f:
            templates = json.load(f)["templates"]

    num_genuine = sample_count // 2
    num_manipulated = sample_count - num_genuine

    all_samples: list[dict[str, Any]] = []

    print(f"Generating {num_genuine} genuine and {num_manipulated} manipulated certificate samples...")

    # 2. Generate Genuine Certificates
    for i in range(num_genuine):
        sample_id = f"GEN_{i+1:05d}"
        tpl = random.choice(templates)
        record = generate_synthetic_record()

        img, field_boxes = render_genuine_certificate(tpl, record, raw_dir, assets_dir)
        filename = f"{sample_id}.png"
        img_path = genuine_dir / filename
        img.save(img_path, "PNG")

        sample_info = {
            "sample_id": sample_id,
            "image_path": str(img_path.relative_to(output_base_dir.parent)),
            "is_manipulated": False,
            "primary_label": "genuine",
            "manipulation_types": [],
            "manipulated_regions": [],
            "source_template": tpl["filename"],
            "source_template_id": tpl["template_id"],
            "base_resolution": list(img.size),
            "ground_truth_fields": {k: v["value"] for k, v in field_boxes.items()},
            "field_bounding_boxes": field_boxes,
        }
        all_samples.append(sample_info)

    # 3. Generate Manipulated Certificates
    for i in range(num_manipulated):
        sample_id = f"MAN_{i+1:05d}"
        tpl = random.choice(templates)
        record = generate_synthetic_record()

        genuine_img, field_boxes = render_genuine_certificate(tpl, record, raw_dir, assets_dir)
        tampered_img, tampered_regions, applied_types = apply_manipulation(
            genuine_img,
            field_boxes,
            assets_dir,
        )

        filename = f"{sample_id}.png"
        img_path = manipulated_dir / filename
        tampered_img.save(img_path, "PNG")

        sample_info = {
            "sample_id": sample_id,
            "image_path": str(img_path.relative_to(output_base_dir.parent)),
            "is_manipulated": True,
            "primary_label": "manipulated",
            "manipulation_types": applied_types,
            "manipulated_regions": tampered_regions,
            "source_template": tpl["filename"],
            "source_template_id": tpl["template_id"],
            "base_resolution": list(tampered_img.size),
            "ground_truth_fields": {k: v["value"] for k, v in field_boxes.items()},
            "field_bounding_boxes": field_boxes,
        }
        all_samples.append(sample_info)

    # 4. Generate Splits & Ground Truth Manifests
    splits = create_dataset_splits(all_samples, output_base_dir)

    # 5. Export Master Metadata CSV
    master_rows = []
    for s in all_samples:
        master_rows.append(
            {
                "sample_id": s["sample_id"],
                "split": s.get("split", "train"),
                "image_path": s["image_path"],
                "is_manipulated": s["is_manipulated"],
                "primary_label": s["primary_label"],
                "manipulation_types": ",".join(s["manipulation_types"]),
                "num_manipulated_regions": len(s["manipulated_regions"]),
                "source_template": s["source_template"],
                "source_template_id": s["source_template_id"],
                "student_name": s["ground_truth_fields"].get("student_name", ""),
                "register_number": s["ground_truth_fields"].get("register_number", ""),
                "certificate_number": s["ground_truth_fields"].get("certificate_number", ""),
                "course_degree": s["ground_truth_fields"].get("course_degree", ""),
                "grade_or_marks": s["ground_truth_fields"].get("grade_or_marks", ""),
            }
        )

    df_master = pd.DataFrame(master_rows)
    master_csv_path = output_base_dir / "metadata.csv"
    df_master.to_csv(master_csv_path, index=False)

    # 6. Copy artifacts to ml/data for ML pipeline consumption
    ml_data_dir.mkdir(parents=True, exist_ok=True)
    df_master.to_csv(ml_data_dir / "metadata.csv", index=False)
    ml_splits_dir = ml_data_dir / "splits"
    ml_splits_dir.mkdir(parents=True, exist_ok=True)
    for split_name in ["train", "val", "test"]:
        src_csv = output_base_dir / "splits" / f"{split_name}.csv"
        if src_csv.exists():
            shutil.copy(src_csv, ml_splits_dir / f"{split_name}.csv")

    summary = {
        "total_generated": len(all_samples),
        "genuine_count": num_genuine,
        "manipulated_count": num_manipulated,
        "splits": {k: len(v) for k, v in splits.items()},
        "metadata_path": str(master_csv_path),
    }
    print("Dataset generation completed successfully!")
    print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic certificate verification dataset.")
    parser.add_argument("--samples", type=int, default=200, help="Total number of certificate samples to generate.")
    parser.add_argument("--output-dir", type=str, default="./datasets", help="Output directory for generated dataset.")
    parser.add_argument("--ml-dir", type=str, default="./ml/data", help="Output directory for ML data files.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    args = parser.parse_args()

    generate_dataset(
        sample_count=args.samples,
        output_base_dir=Path(args.output_dir),
        ml_data_dir=Path(args.ml_dir),
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
