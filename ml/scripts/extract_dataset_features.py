from pathlib import Path

import numpy as np
import pandas as pd


def generate_synthetic_feature_dataset(
    n_samples: int = 600,
    manipulated_ratio: float = 0.50,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Synthesize realistic 22D tabular feature distributions for genuine and manipulated certificates.

    Used to augment dataset splits for robust machine learning model training and evaluation.

    Args:
        n_samples: Total number of samples across train, val, and test splits.
        manipulated_ratio: Fraction of manipulated (positive class) samples.
        random_state: Seed for reproducibility.

    Returns:
        Tuple of (train_df, val_df, test_df) containing the 22 features and 'is_manipulated'.
    """
    rng = np.random.default_rng(random_state)
    n_fake = int(n_samples * manipulated_ratio)
    n_genuine = n_samples - n_fake

    # --------------------------------------------------------------------------
    # Genuine Samples Generation (High scores, uniform compression, no clones)
    # --------------------------------------------------------------------------
    genuine_data: dict[str, np.ndarray] = {
        # Group A: Ingestion & Metadata
        "file_size_kb": rng.normal(loc=1200.0, scale=300.0, size=n_genuine).clip(
            200.0, 5000.0
        ),
        "has_exif": rng.choice([1.0, 0.0], p=[0.75, 0.25], size=n_genuine),
        "software_editing_flag": rng.choice([0.0, 1.0], p=[0.96, 0.04], size=n_genuine),
        "aspect_ratio_deviation": rng.exponential(scale=0.03, size=n_genuine).clip(
            0.0, 0.15
        ),
        # Group B: OCR & Text Quality
        "ocr_mean_confidence": rng.normal(loc=0.92, scale=0.04, size=n_genuine).clip(
            0.80, 0.99
        ),
        "ocr_min_confidence": rng.normal(loc=0.82, scale=0.05, size=n_genuine).clip(
            0.70, 0.95
        ),
        "flagged_field_count": rng.poisson(lam=0.15, size=n_genuine)
        .clip(0, 2)
        .astype(float),
        "missing_critical_fields_count": rng.choice(
            [0.0, 1.0], p=[0.97, 0.03], size=n_genuine
        ),
        # Group C: Text Consistency
        "baseline_alignment_score": rng.normal(
            loc=0.94, scale=0.04, size=n_genuine
        ).clip(0.82, 1.0),
        "font_size_consistency_score": rng.normal(
            loc=0.95, scale=0.03, size=n_genuine
        ).clip(0.85, 1.0),
        "stroke_weight_score": rng.normal(loc=0.92, scale=0.04, size=n_genuine).clip(
            0.80, 1.0
        ),
        "character_spacing_score": rng.normal(
            loc=0.93, scale=0.04, size=n_genuine
        ).clip(0.80, 1.0),
        "logical_consistency_score": rng.normal(
            loc=0.98, scale=0.02, size=n_genuine
        ).clip(0.90, 1.0),
        # Group D: Image Forensics
        "ela_score": rng.normal(loc=0.94, scale=0.04, size=n_genuine).clip(0.82, 1.0),
        "copy_move_score": rng.normal(loc=0.98, scale=0.02, size=n_genuine).clip(
            0.90, 1.0
        ),
        "cloned_regions_count": np.zeros(n_genuine, dtype=float),
        "noise_inconsistency_score": rng.normal(
            loc=0.93, scale=0.04, size=n_genuine
        ).clip(0.80, 1.0),
        # Group E: Template & Record Matching
        "template_ssim_score": rng.normal(loc=0.91, scale=0.05, size=n_genuine).clip(
            0.80, 1.0
        ),
        "template_feature_score": rng.normal(loc=0.88, scale=0.06, size=n_genuine).clip(
            0.70, 1.0
        ),
        "seal_match_score": rng.normal(loc=0.92, scale=0.04, size=n_genuine).clip(
            0.80, 1.0
        ),
        "record_found_flag": rng.choice([1.0, 0.0], p=[0.70, 0.30], size=n_genuine),
        "record_match_score": rng.normal(loc=0.95, scale=0.05, size=n_genuine).clip(
            0.70, 1.0
        ),
        "is_manipulated": np.zeros(n_genuine, dtype=int),
    }

    # --------------------------------------------------------------------------
    # Manipulated Samples Generation (Defects across text, forensics, or template)
    # --------------------------------------------------------------------------
    # Synthesize different forgery archetypes: Text Tampering, Clones, Splicing, Recompression
    fake_data: dict[str, np.ndarray] = {
        # Group A: Ingestion & Metadata
        "file_size_kb": rng.normal(loc=850.0, scale=400.0, size=n_fake).clip(
            100.0, 6000.0
        ),
        "has_exif": rng.choice([1.0, 0.0], p=[0.40, 0.60], size=n_fake),
        "software_editing_flag": rng.choice([1.0, 0.0], p=[0.65, 0.35], size=n_fake),
        "aspect_ratio_deviation": rng.exponential(scale=0.08, size=n_fake).clip(
            0.0, 0.50
        ),
        # Group B: OCR & Text Quality
        "ocr_mean_confidence": rng.normal(loc=0.74, scale=0.10, size=n_fake).clip(
            0.40, 0.90
        ),
        "ocr_min_confidence": rng.normal(loc=0.55, scale=0.15, size=n_fake).clip(
            0.20, 0.80
        ),
        "flagged_field_count": rng.poisson(lam=2.4, size=n_fake)
        .clip(0, 6)
        .astype(float),
        "missing_critical_fields_count": rng.poisson(lam=0.8, size=n_fake)
        .clip(0, 4)
        .astype(float),
        # Group C: Text Consistency (Strong anomaly signals)
        "baseline_alignment_score": rng.normal(loc=0.62, scale=0.14, size=n_fake).clip(
            0.20, 0.85
        ),
        "font_size_consistency_score": rng.normal(
            loc=0.60, scale=0.15, size=n_fake
        ).clip(0.20, 0.82),
        "stroke_weight_score": rng.normal(loc=0.58, scale=0.16, size=n_fake).clip(
            0.20, 0.82
        ),
        "character_spacing_score": rng.normal(loc=0.64, scale=0.14, size=n_fake).clip(
            0.25, 0.85
        ),
        "logical_consistency_score": rng.normal(loc=0.50, scale=0.25, size=n_fake).clip(
            0.0, 0.90
        ),
        # Group D: Image Forensics (ELA & Clone spikes)
        "ela_score": rng.normal(loc=0.48, scale=0.18, size=n_fake).clip(0.10, 0.80),
        "copy_move_score": rng.choice(
            [rng.uniform(0.15, 0.55), rng.uniform(0.85, 0.95)],
            p=[0.60, 0.40],
            size=n_fake,
        ),
        "cloned_regions_count": rng.choice(
            [1.0, 2.0, 3.0, 0.0], p=[0.40, 0.20, 0.10, 0.30], size=n_fake
        ),
        "noise_inconsistency_score": rng.normal(loc=0.55, scale=0.18, size=n_fake).clip(
            0.15, 0.82
        ),
        # Group E: Template & Record Matching
        "template_ssim_score": rng.normal(loc=0.55, scale=0.16, size=n_fake).clip(
            0.20, 0.80
        ),
        "template_feature_score": rng.normal(loc=0.52, scale=0.18, size=n_fake).clip(
            0.15, 0.78
        ),
        "seal_match_score": rng.normal(loc=0.46, scale=0.20, size=n_fake).clip(
            0.10, 0.75
        ),
        "record_found_flag": rng.choice([0.0, 1.0], p=[0.85, 0.15], size=n_fake),
        "record_match_score": rng.normal(loc=0.35, scale=0.20, size=n_fake).clip(
            0.0, 0.70
        ),
        "is_manipulated": np.ones(n_fake, dtype=int),
    }

    df_genuine = pd.DataFrame(genuine_data)
    df_fake = pd.DataFrame(fake_data)
    df_all = pd.concat([df_genuine, df_fake], ignore_index=True)

    # Shuffle
    df_all = df_all.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    # Split: 70% Train, 15% Val, 15% Test
    n_train = int(len(df_all) * 0.70)
    n_val = int(len(df_all) * 0.15)

    train_df = df_all.iloc[:n_train].reset_index(drop=True)
    val_df = df_all.iloc[n_train : n_train + n_val].reset_index(drop=True)
    test_df = df_all.iloc[n_train + n_val :].reset_index(drop=True)

    return train_df, val_df, test_df


def extract_and_save_dataset_features(
    output_dir: Path | None = None,
    n_samples: int = 600,
) -> tuple[Path, Path, Path]:
    """Generate and persist tabular feature tables for train, validation, and test splits."""
    out_dir = output_dir or Path("ml/data")
    out_dir.mkdir(parents=True, exist_ok=True)

    train_df, val_df, test_df = generate_synthetic_feature_dataset(n_samples=n_samples)

    train_path = out_dir / "features_train.csv"
    val_path = out_dir / "features_val.csv"
    test_path = out_dir / "features_test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    return train_path, val_path, test_path


if __name__ == "__main__":
    t_path, v_path, te_path = extract_and_save_dataset_features()
    print(f"Extracted feature datasets:\n - {t_path}\n - {v_path}\n - {te_path}")
