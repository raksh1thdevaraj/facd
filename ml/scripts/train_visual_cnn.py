"""Two-stage transfer learning training script for certificate visual CNN model."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.modules.visual_model.network import CertificateVisualCNN

from ml.scripts.dataset_loader import create_dataloaders

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def evaluate_epoch(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float, float, float, float]:
    """Evaluate model on validation loader, returning loss and classification metrics."""
    model.eval()
    total_loss = 0.0
    all_targets: list[float] = []
    all_preds: list[int] = []

    with torch.no_grad():
        for batch in val_loader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)
            logits, _ = model(images)
            loss = criterion(logits, labels)
            total_loss += loss.item() * len(labels)

            probs = torch.sigmoid(logits).cpu().numpy()
            preds = (probs >= 0.5).astype(int)
            all_preds.extend(preds.tolist())
            all_targets.extend(labels.cpu().numpy().tolist())

    n_samples = max(1, len(all_targets))
    mean_loss = total_loss / n_samples
    acc = float(accuracy_score(all_targets, all_preds)) if all_targets else 0.0
    prec = (
        float(precision_score(all_targets, all_preds, zero_division=0))
        if all_targets
        else 0.0
    )
    rec = (
        float(recall_score(all_targets, all_preds, zero_division=0))
        if all_targets
        else 0.0
    )
    f1 = (
        float(f1_score(all_targets, all_preds, zero_division=0)) if all_targets else 0.0
    )

    return mean_loss, acc, prec, rec, f1


def train_visual_cnn(
    config_path: str | Path = "ml/configs/dl_model_config.json",
    epochs_stage1_override: int | None = None,
    epochs_stage2_override: int | None = None,
    device_override: str | None = None,
) -> dict[str, Any]:
    """Run two-stage transfer learning pipeline."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    epochs_s1 = (
        epochs_stage1_override
        if epochs_stage1_override is not None
        else config.get("epochs_stage1", 3)
    )
    epochs_s2 = (
        epochs_stage2_override
        if epochs_stage2_override is not None
        else config.get("epochs_stage2", 5)
    )

    if device_override:
        device = torch.device(device_override)
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    logger.info("Training on device: %s", device)

    train_loader, val_loader, _ = create_dataloaders(config, base_dir=PROJECT_ROOT)

    model = CertificateVisualCNN(
        backbone_name=config.get("backbone", "efficientnet_b0"),
        pretrained=config.get("pretrained", True),
        embedding_dim=config.get("embedding_dim", 512),
    ).to(device)

    criterion = nn.BCEWithLogitsLoss()
    best_val_f1 = -1.0
    history: dict[str, list[float]] = {
        "train_loss": [],
        "val_loss": [],
        "val_accuracy": [],
        "val_f1": [],
    }

    save_path = PROJECT_ROOT / config.get(
        "model_save_path", "ml/models/visual_cnn_best.pt"
    )
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # ================= Stage 1: Train Custom Head =================
    logger.info(
        "--- Starting Stage 1: Feature Extraction (Backbone Frozen, %d epochs) ---",
        epochs_s1,
    )
    model.freeze_backbone()
    optimizer_s1 = AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=config.get("lr_head", 1e-3),
        weight_decay=config.get("weight_decay", 1e-2),
    )

    for epoch in range(1, epochs_s1 + 1):
        model.train()
        running_loss = 0.0
        n_samples = 0
        for batch in train_loader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)
            optimizer_s1.zero_grad()
            logits, _ = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer_s1.step()

            running_loss += loss.item() * len(labels)
            n_samples += len(labels)

        train_loss = running_loss / max(1, n_samples)
        val_loss, val_acc, _val_prec, _val_rec, val_f1 = evaluate_epoch(
            model, val_loader, criterion, device
        )

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_accuracy"].append(val_acc)
        history["val_f1"].append(val_f1)

        logger.info(
            "Stage 1 Epoch %d/%d - Train Loss: %.4f, Val Loss: %.4f, Val Acc: %.4f, Val F1: %.4f",
            epoch,
            epochs_s1,
            train_loss,
            val_loss,
            val_acc,
            val_f1,
        )

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save(
                {
                    "state_dict": model.state_dict(),
                    "backbone": config.get("backbone", "efficientnet_b0"),
                    "embedding_dim": config.get("embedding_dim", 512),
                    "epoch": epoch,
                    "stage": 1,
                    "val_f1": val_f1,
                },
                save_path,
            )

    # ================= Stage 2: Fine-Tuning =================
    logger.info("--- Starting Stage 2: Fine-Tuning (%d epochs) ---", epochs_s2)
    model.unfreeze_backbone(top_blocks_only=True)
    optimizer_s2 = AdamW(
        [
            {
                "params": model.backbone.parameters(),
                "lr": config.get("lr_backbone", 5e-5),
            },
            {
                "params": model.embedding_layer.parameters(),
                "lr": config.get("lr_head", 5e-4),
            },
            {
                "params": model.classifier.parameters(),
                "lr": config.get("lr_head", 5e-4),
            },
        ],
        weight_decay=config.get("weight_decay", 1e-2),
    )
    scheduler = CosineAnnealingLR(optimizer_s2, T_max=max(1, epochs_s2), eta_min=1e-6)

    for epoch in range(1, epochs_s2 + 1):
        model.train()
        running_loss = 0.0
        n_samples = 0
        for batch in train_loader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)
            optimizer_s2.zero_grad()
            logits, _ = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer_s2.step()

            running_loss += loss.item() * len(labels)
            n_samples += len(labels)

        scheduler.step()
        train_loss = running_loss / max(1, n_samples)
        val_loss, val_acc, _val_prec, _val_rec, val_f1 = evaluate_epoch(
            model, val_loader, criterion, device
        )

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_accuracy"].append(val_acc)
        history["val_f1"].append(val_f1)

        logger.info(
            "Stage 2 Epoch %d/%d - Train Loss: %.4f, Val Loss: %.4f, Val Acc: %.4f, Val F1: %.4f",
            epoch,
            epochs_s2,
            train_loss,
            val_loss,
            val_acc,
            val_f1,
        )

        if val_f1 >= best_val_f1:
            best_val_f1 = val_f1
            torch.save(
                {
                    "state_dict": model.state_dict(),
                    "backbone": config.get("backbone", "efficientnet_b0"),
                    "embedding_dim": config.get("embedding_dim", 512),
                    "epoch": epoch,
                    "stage": 2,
                    "val_f1": val_f1,
                },
                save_path,
            )

    # Save training history
    history_path = PROJECT_ROOT / config.get(
        "history_report_path", "ml/reports/dl_training_history.json"
    )
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    logger.info(
        "Training complete. Best checkpoint saved to %s (Best Val F1: %.4f)",
        save_path,
        best_val_f1,
    )
    return {
        "best_val_f1": best_val_f1,
        "history": history,
        "model_path": str(save_path),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Certificate Visual CNN")
    parser.add_argument("--config", default="ml/configs/dl_model_config.json")
    parser.add_argument("--epochs-s1", type=int, default=None)
    parser.add_argument("--epochs-s2", type=int, default=None)
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    train_visual_cnn(
        config_path=args.config,
        epochs_stage1_override=args.epochs_s1,
        epochs_stage2_override=args.epochs_s2,
        device_override=args.device,
    )
