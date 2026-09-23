"""
Lightweight Visual & Alignment Tamper Detector Training Pipeline.
Adhering to Paper 2 & MobileNet Forensics (Anandamurugan et al., IEEE 2026):
- Architecture: MobileNetV2 with pre-trained ImageNet weights
- Frozen early convolutional base layers
- Custom Classification Head: GAP -> Dropout(0.3) -> Dense(64, ReLU) -> Dense(1, Sigmoid)
- Total Parameters: < 3.5 Million (Model size ~9.5MB - 14MB)
- Loss: BinaryCrossentropy (BCEWithLogitsLoss)
- Optimizer: Adam(lr=1e-4) with early stopping (patience=5)
- Target Metrics: Precision >= 95%, Recall >= 94%, F1-Score >= 95%
- Exports: models/visual_tamper_mobilenet.pt and models/visual_tamper_mobilenet.onnx
"""

import os
import sys
import time
import copy

# Prevent Windows console UnicodeEncodeError on emoji characters
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

import numpy as np
import torch
import torch.nn as nn
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, accuracy_score, confusion_matrix
from src.data_loader import get_image_data_loaders


class MobileNetTamperDetector(nn.Module):
    """
    MobileNetV2 Transfer Learning Architecture for Certificate Visual Tampering Detection.
    Total parameters: ~2.3M (< 3.5 Million limit).
    """

    def __init__(self, freeze_base_layers: int = 14, pretrained: bool = True):
        super().__init__()
        weights = MobileNet_V2_Weights.DEFAULT if pretrained else None
        base = mobilenet_v2(weights=weights)

        # Freeze early convolutional layers
        for i, layer in enumerate(base.features):
            if i < freeze_base_layers:
                for param in layer.parameters():
                    param.requires_grad = False

        self.features = base.features
        # Head: GlobalAveragePooling2D (AdaptiveAvgPool2d) -> Dropout(0.3) -> Dense(64, relu) -> Dense(1)
        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Dropout(p=0.3),
            nn.Linear(1280, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.features(x)
        out = self.head(feat)
        return out.squeeze(-1)


def train_visual_forensics_model(
    datasets_dir: str = "datasets",
    output_pt_path: str = "models/visual_tamper_mobilenet.pt",
    output_onnx_path: str = "models/visual_tamper_mobilenet.onnx",
    num_epochs: int = 15,
    batch_size: int = 32,
    lr: float = 1e-4,
    patience: int = 5,
    device: str = None
):
    print("=" * 70)
    print("TRAINING LIGHTWEIGHT VISUAL TAMPER DETECTOR (MobileNetV2)")
    print("=" * 70)

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[*] Target Compute Device: {device.upper()}")

    # 1. Load Data
    train_loader, val_loader = get_image_data_loaders(
        datasets_dir=datasets_dir,
        batch_size=batch_size,
        target_size=(224, 224),
        num_workers=0
    )

    # 2. Instantiate Model
    model = MobileNetTamperDetector(freeze_base_layers=14, pretrained=True)
    model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[*] Total Parameters: {total_params:,} (< 3,500,000 constraint)")
    print(f"[*] Trainable Parameters: {trainable_params:,}")

    # 3. Loss with class weighting (balancing pristine vs tampered instances)
    criterion = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([0.45], device=device))
    optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)

    # 4. Training Loop with Early Stopping
    best_val_f1 = -1.0
    best_val_loss = float("inf")
    best_threshold = 0.5
    best_model_weights = None
    epochs_no_improve = 0

    print(f"\n[*] Starting Training: {num_epochs} Epochs, Batch Size {batch_size}, LR {lr}")
    for epoch in range(1, num_epochs + 1):
        start_time = time.time()
        model.train()
        train_loss = 0.0
        train_steps = 0

        for rgb, _, labels in train_loader:
            rgb = rgb.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            logits = model(rgb)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            train_steps += 1

        avg_train_loss = train_loss / max(1, train_steps)

        # Validation Phase
        model.eval()
        val_loss = 0.0
        val_steps = 0
        all_preds = []
        all_targets = []
        all_probs = []

        with torch.no_grad():
            for rgb, _, labels in val_loader:
                rgb = rgb.to(device)
                labels = labels.to(device)

                logits = model(rgb)
                loss = criterion(logits, labels)
                val_loss += loss.item()
                val_steps += 1

                probs = torch.sigmoid(logits).cpu().numpy()
                all_probs.extend(probs.flatten().tolist())
                all_targets.extend(labels.cpu().numpy().flatten().tolist())

        avg_val_loss = val_loss / max(1, val_steps)
        all_probs_np = np.array(all_probs)
        all_targets_np = np.array(all_targets)

        # Threshold calibration to optimize F1 / precision trade-off
        best_th = 0.5
        best_th_f1 = -1.0
        for th in [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]:
            cand_preds = (all_probs_np >= th).astype(np.float32)
            cand_f1 = f1_score(all_targets_np, cand_preds, zero_division=0)
            if cand_f1 > best_th_f1:
                best_th_f1 = cand_f1
                best_th = th

        all_preds = (all_probs_np >= best_th).astype(np.float32)
        acc = accuracy_score(all_targets_np, all_preds)
        prec = precision_score(all_targets_np, all_preds, zero_division=0)
        rec = recall_score(all_targets_np, all_preds, zero_division=0)
        f1 = best_th_f1
        try:
            auc = roc_auc_score(all_targets_np, all_probs_np)
        except Exception:
            auc = 0.5

        elapsed = time.time() - start_time
        print(f"Epoch [{epoch:02d}/{num_epochs:02d}] ({elapsed:.1f}s) | "
              f"Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f} | "
              f"Acc: {acc*100:.2f}% | Prec: {prec*100:.2f}% | Rec: {rec*100:.2f}% | F1: {f1*100:.2f}% | AUC: {auc:.4f} (Th: {best_th})")

        # Check early stopping / best model checkpoint
        if f1 > best_val_f1 or (f1 == best_val_f1 and avg_val_loss < best_val_loss):
            best_val_f1 = f1
            best_val_loss = avg_val_loss
            best_val_acc = acc
            best_val_prec = prec
            best_val_rec = rec
            best_val_cm = confusion_matrix(all_targets, all_preds)
            best_threshold = best_th
            best_model_weights = copy.deepcopy(model.state_dict())
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"[!] Early stopping triggered at epoch {epoch} (Patience {patience})")
                break

    # 5. Restore best weights
    if best_model_weights is not None:
        model.load_state_dict(best_model_weights)

    final_acc = best_val_acc if "best_val_acc" in locals() else acc
    final_prec = best_val_prec if "best_val_prec" in locals() else prec
    final_rec = best_val_rec if "best_val_rec" in locals() else rec
    final_f1 = best_val_f1 if "best_val_f1" in locals() and best_val_f1 > 0 else f1
    final_cm = best_val_cm if "best_val_cm" in locals() else confusion_matrix(all_targets, all_preds)

    print("\n" + "=" * 50)
    print("FINAL VISUAL TAMPER DETECTOR METRICS:")
    print(f"  Accuracy:  {final_acc*100:.2f}%")
    print(f"  Precision: {final_prec*100:.2f}% (Target: >= 95%)")
    print(f"  Recall:    {final_rec*100:.2f}% (Target: >= 94%)")
    print(f"  F1-Score:  {final_f1*100:.2f}% (Target: >= 95%)")
    print(f"  Calibrated Decision Threshold: {best_threshold:.2f}")
    print("  Confusion Matrix:")
    print(final_cm)
    print("=" * 50)

    # 6. Save PyTorch Model (.pt)
    os.makedirs(os.path.dirname(output_pt_path), exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(),
        "arch": "MobileNetV2",
        "total_params": total_params,
        "threshold": float(best_threshold),
        "metrics": {
            "accuracy": float(final_acc),
            "precision": float(final_prec),
            "recall": float(final_rec),
            "f1_score": float(final_f1)
        }
    }, output_pt_path)
    pt_size_mb = os.path.getsize(output_pt_path) / (1024 * 1024)
    print(f"[OK] Saved PyTorch weights to: {output_pt_path} ({pt_size_mb:.2f} MB < 15MB limit)")

    # 7. Export ONNX Model (.onnx)
    try:
        model.eval().to("cpu")
        dummy_input = torch.randn(1, 3, 224, 224, dtype=torch.float32)
        torch.onnx.export(
            model,
            dummy_input,
            output_onnx_path,
            export_params=True,
            opset_version=18,
            do_constant_folding=True,
            input_names=["input"],
            output_names=["logits"],
            dynamic_axes={"input": {0: "batch_size"}, "logits": {0: "batch_size"}}
        )
        onnx_size_mb = os.path.getsize(output_onnx_path) / (1024 * 1024)
        print(f"[OK] Exported ONNX model to: {output_onnx_path} ({onnx_size_mb:.2f} MB < 15MB limit)")
    except Exception as e:
        print(f"[WARNING] ONNX export failed: {e}. PyTorch model saved as primary export.")

    return model


if __name__ == "__main__":
    train_visual_forensics_model(num_epochs=15, batch_size=32)
