"""Dataset Statistics Reporter.

Computes and prints detailed statistics regarding class distributions,
manipulation techniques breakdown, template allocations, and split ratios.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def print_dataset_stats(dataset_dir: Path) -> None:
    """Read metadata and print formatted summary tables."""
    metadata_path = dataset_dir / "metadata.csv"
    if not metadata_path.exists():
        print(f"Error: metadata.csv not found at {metadata_path}")
        return

    df = pd.read_csv(metadata_path)
    total = len(df)
    print("=" * 60)
    print(f" CERTIFICATE VERIFICATION DATASET SUMMARY (Total: {total})")
    print("=" * 60)

    # Class distribution
    print("\n1. Class Distribution:")
    class_counts = df["primary_label"].value_counts()
    for label, count in class_counts.items():
        print(f"   • {label.capitalize():<15}: {count:4d} ({count / total:.1%})")

    # Split distribution
    print("\n2. Split Distribution:")
    split_counts = df["split"].value_counts()
    for split_name, count in split_counts.items():
        print(f"   • {split_name.capitalize():<15}: {count:4d} ({count / total:.1%})")

    # Template distribution
    print("\n3. Source Template Distribution:")
    tpl_counts = df["source_template_id"].value_counts()
    for tpl_id, count in tpl_counts.items():
        print(f"   • {tpl_id:<28}: {count:4d} ({count / total:.1%})")

    # Tampering Techniques
    manip_df = df[df["is_manipulated"]]
    if not manip_df.empty and "manipulation_types" in manip_df.columns:
        print("\n4. Tampering Techniques Distribution:")
        tech_counts: dict[str, int] = {}
        for types_str in manip_df["manipulation_types"].dropna():
            for t in str(types_str).split(","):
                t = t.strip()
                if t:
                    tech_counts[t] = tech_counts.get(t, 0) + 1
        for tech, count in tech_counts.items():
            print(f"   • {tech:<28}: {count:4d} ({count / len(manip_df):.1%})")

    print("\n" + "=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Print dataset statistics.")
    parser.add_argument("--dataset-dir", type=str, default="./datasets", help="Path to dataset directory.")
    args = parser.parse_args()
    print_dataset_stats(Path(args.dataset_dir))


if __name__ == "__main__":
    main()
