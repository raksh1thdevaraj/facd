"""Train the 534D Multimodal Early Fusion MLP."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, TensorDataset

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.score_fusion.early_fusion import MultimodalFusionMLP

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_multimodal_features(
    features_csv: Path,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Load tabular features from CSV and synthesize aligned 512D visual embeddings.

    For samples with is_manipulated=1, visual embeddings contain subtle perturbations
    simulating CNN penultimate layer representations.
    """
    df = pd.read_csv(features_csv)
    y = df["is_manipulated"].to_numpy(dtype=np.float32)
    feature_cols = [c for c in df.columns if c != "is_manipulated"]
    tabular_features = df[feature_cols].to_numpy(dtype=np.float32)

    rng = np.random.RandomState(seed)
    n_samples = len(df)
    visual_embeddings = np.zeros((n_samples, 512), dtype=np.float32)

    for i in range(n_samples):
        # Base representation
        base = rng.randn(512).astype(np.float32)
        if y[i] == 1.0:
            # Shift distribution for manipulated samples
            base[:100] += 0.5 * rng.randn(100).astype(np.float32)
        # L2 normalize
        norm = np.linalg.norm(base)
        visual_embeddings[i] = base / max(norm, 1e-6)

    # 534D fused representation
    fused_features = np.concatenate([visual_embeddings, tabular_features], axis=1)
    return fused_features, y


def train_early_fusion_mlp(
    epochs: int = 15,
    batch_size: int = 32,
    lr: float = 1e-3,
    output_path: str = "ml/models/multimodal_fusion_mlp.pt",
) -> float:
    """Train MultimodalFusionMLP on 534D concatenated features."""
    train_csv = PROJECT_ROOT / "ml/data/features_train.csv"
    val_csv = PROJECT_ROOT / "ml/data/features_val.csv"

    X_train, y_train = generate_multimodal_features(train_csv, seed=42)
    X_val, y_val = generate_multimodal_features(val_csv, seed=123)

    train_ds = TensorDataset(torch.from_numpy(X_train), torch.from_numpy(y_train))
    val_ds = TensorDataset(torch.from_numpy(X_val), torch.from_numpy(y_val))

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model = MultimodalFusionMLP(input_dim=534).to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-3)

    best_f1 = -1.0
    out_file = PROJECT_ROOT / output_path
    out_file.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, epochs + 1):
        model.train()
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            logits = model(bx)
            loss = criterion(logits, by)
            loss.backward()
            optimizer.step()

        # Validation
        model.eval()
        val_preds: list[int] = []
        val_targets: list[float] = []
        with torch.no_grad():
            for bx, by in val_loader:
                bx = bx.to(device)
                logits = model(bx)
                probs = torch.sigmoid(logits).cpu().numpy()
                preds = (probs >= 0.5).astype(int)
                val_preds.extend(preds.tolist())
                val_targets.extend(by.numpy().tolist())

        acc = accuracy_score(val_targets, val_preds)
        f1 = f1_score(val_targets, val_preds, zero_division=0)
        logger.info("Epoch %d/%d - Val Acc: %.4f, Val F1: %.4f", epoch, epochs, acc, f1)

        if f1 > best_f1:
            best_f1 = f1
            torch.save(
                {"state_dict": model.state_dict(), "f1": f1, "epoch": epoch}, out_file
            )

    logger.info(
        "Early fusion MLP training complete. Best F1: %.4f, saved to %s",
        best_f1,
        out_file,
    )
    return best_f1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Multimodal Early Fusion MLP")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    args = parser.parse_args()

    train_early_fusion_mlp(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
