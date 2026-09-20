"""Train Stacking Meta-Classifier on branch predictions."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.score_fusion.meta_classifier import StackingMetaClassifier

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def extract_meta_features_from_csv(csv_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Derive 5 meta-features from tabular dataset features:

    [visual_fake_prob, tabular_fake_prob, forensic_score, text_consistency_score, template_score]
    Target y: 1 = Authentic, 0 = Manipulated.
    """
    df = pd.read_csv(csv_path)
    is_manipulated = df["is_manipulated"].to_numpy(dtype=np.int32)
    y = 1 - is_manipulated  # 1 = Authentic, 0 = Manipulated

    # Visual fake prob correlates with ela/copy-move/noise
    visual_fake = np.clip(
        0.5 * (1.0 - df["ela_score"])
        + 0.5 * (1.0 - df["copy_move_score"])
        + 0.1 * np.random.randn(len(df)),
        0.0,
        1.0,
    )
    # Tabular fake prob correlates with logical consistency and ocr
    tabular_fake = np.clip(
        0.5 * (1.0 - df["logical_consistency_score"])
        + 0.5 * (1.0 - df["ocr_mean_confidence"]),
        0.0,
        1.0,
    )

    forensic = df["ela_score"].to_numpy(dtype=np.float32)
    text_consistency = df["logical_consistency_score"].to_numpy(dtype=np.float32)
    template = df["template_ssim_score"].to_numpy(dtype=np.float32)

    X = np.column_stack(
        [visual_fake, tabular_fake, forensic, text_consistency, template]
    ).astype(np.float32)
    return X, y


def train_meta_classifier(
    train_csv: str = "ml/data/features_train.csv",
    output_path: str = "ml/models/meta_classifier.joblib",
) -> None:
    """Train and serialize StackingMetaClassifier."""
    X_train, y_train = extract_meta_features_from_csv(PROJECT_ROOT / train_csv)
    clf = StackingMetaClassifier()
    clf.fit(X_train, y_train)

    out_file = PROJECT_ROOT / output_path
    clf.save(out_file)
    logger.info(
        "Stacking meta-classifier successfully trained and saved to %s", out_file
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Stacking Meta-Classifier")
    parser.add_argument("--train-csv", default="ml/data/features_train.csv")
    parser.add_argument("--output", default="ml/models/meta_classifier.joblib")
    args = parser.parse_args()

    train_meta_classifier(train_csv=args.train_csv, output_path=args.output)
