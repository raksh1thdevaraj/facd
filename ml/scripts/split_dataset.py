"""Dataset Splitter & Ground Truth Manifest Generator.

Partitions generated samples into Train (70%), Val (15%), and Test (15%) splits
with template leakage prevention and produces SPEC-04 compliant JSON & CSV manifests.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def create_dataset_splits(
    samples: list[dict[str, Any]],
    output_dir: Path,
    ood_template_id: str = "template_national_academy",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> dict[str, list[dict[str, Any]]]:
    """Split samples into train, val, and test partitions with out-of-distribution isolation."""
    ground_truth_dir = output_dir / "ground_truth"
    splits_dir = output_dir / "splits"
    ground_truth_dir.mkdir(parents=True, exist_ok=True)
    splits_dir.mkdir(parents=True, exist_ok=True)

    # 1. Separate OOD template samples for test split
    ood_samples = [s for s in samples if s.get("source_template_id") == ood_template_id]
    in_dist_samples = [
        s for s in samples if s.get("source_template_id") != ood_template_id
    ]

    # 2. Stratify in-distribution samples by label
    genuine = [s for s in in_dist_samples if not s["is_manipulated"]]
    manipulated = [s for s in in_dist_samples if s["is_manipulated"]]

    # Shuffle deterministically
    import random

    rng = random.Random(42)
    rng.shuffle(genuine)
    rng.shuffle(manipulated)

    def split_group(
        group: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        n = len(group)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        return (
            group[:n_train],
            group[n_train : n_train + n_val],
            group[n_train + n_val :],
        )

    g_train, g_val, g_test = split_group(genuine)
    m_train, m_val, m_test = split_group(manipulated)

    train_samples = g_train + m_train
    val_samples = g_val + m_val
    test_samples = g_test + m_test + ood_samples

    rng.shuffle(train_samples)
    rng.shuffle(val_samples)
    rng.shuffle(test_samples)

    splits = {
        "train": train_samples,
        "val": val_samples,
        "test": test_samples,
    }

    timestamp = datetime.now(timezone.utc).isoformat()

    # 3. Export JSON Manifests and CSV files
    for split_name, split_list in splits.items():
        # Update split field on each sample
        for item in split_list:
            item["split"] = split_name

        manifest_data = {
            "dataset_version": "1.0.0",
            "generated_at": timestamp,
            "split": split_name,
            "total_samples": len(split_list),
            "genuine_count": sum(1 for s in split_list if not s["is_manipulated"]),
            "manipulated_count": sum(1 for s in split_list if s["is_manipulated"]),
            "samples": split_list,
        }

        # Save JSON manifest
        json_path = ground_truth_dir / f"{split_name}_manifest.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        # Save CSV split file
        rows = []
        for s in split_list:
            rows.append(
                {
                    "sample_id": s["sample_id"],
                    "split": s["split"],
                    "image_path": s["image_path"],
                    "is_manipulated": s["is_manipulated"],
                    "primary_label": s["primary_label"],
                    "manipulation_types": ",".join(s.get("manipulation_types", [])),
                    "source_template": s.get("source_template", ""),
                    "source_template_id": s.get("source_template_id", ""),
                }
            )
        df = pd.DataFrame(rows)
        df.to_csv(splits_dir / f"{split_name}.csv", index=False)

    return splits
