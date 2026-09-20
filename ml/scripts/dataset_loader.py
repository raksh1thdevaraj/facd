"""PyTorch Dataset and DataLoader for certificate images."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import torch
from app.modules.visual_model.transforms import (
    get_inference_transforms,
    get_train_transforms,
)
from PIL import Image
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler


class CertificateImageDataset(Dataset):
    """PyTorch Dataset loading certificate images from split CSV manifests."""

    def __init__(
        self,
        manifest_path: str | Path,
        transform: Any | None = None,
        base_dir: str | Path = ".",
    ) -> None:
        self.base_dir = Path(base_dir)
        self.df = pd.read_csv(manifest_path)
        self.transform = transform

        # Validate required columns
        if (
            "image_path" not in self.df.columns
            or "is_manipulated" not in self.df.columns
        ):
            raise ValueError(
                f"Manifest {manifest_path} must contain 'image_path' and 'is_manipulated'"
            )

        # Ensure label is float 0.0 (genuine) or 1.0 (manipulated)
        self.labels = [
            1.0 if str(val).lower() in ("true", "1", "manipulated") else 0.0
            for val in self.df["is_manipulated"]
        ]

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        row = self.df.iloc[idx]
        rel_path = row["image_path"]
        img_full_path = self.base_dir / rel_path

        if not img_full_path.exists():
            raise FileNotFoundError(f"Image not found: {img_full_path}")

        with Image.open(img_full_path) as img:
            if img.mode != "RGB":
                img = img.convert("RGB")
            if self.transform is not None:
                tensor = self.transform(img)
            else:
                tensor = get_inference_transforms()(img)

        label = torch.tensor(self.labels[idx], dtype=torch.float32)

        return {
            "image": tensor,
            "label": label,
            "path": str(img_full_path),
            "sample_id": str(row.get("sample_id", f"sample_{idx}")),
        }


def create_dataloaders(
    config: dict[str, Any],
    base_dir: str | Path = ".",
    splits_dir: str | Path = "ml/data/splits",
) -> tuple[DataLoader, DataLoader, DataLoader]:
    """Create train, validation, and test DataLoaders with balanced sampling."""
    base_dir = Path(base_dir)
    splits_dir = Path(splits_dir)

    train_csv = splits_dir / "train.csv"
    val_csv = splits_dir / "val.csv"
    test_csv = splits_dir / "test.csv"

    image_size = config.get("image_size", 512)
    batch_size = config.get("batch_size", 8)
    num_workers = config.get("num_workers", 0)

    train_dataset = CertificateImageDataset(
        manifest_path=train_csv,
        transform=get_train_transforms(image_size),
        base_dir=base_dir,
    )
    val_dataset = CertificateImageDataset(
        manifest_path=val_csv,
        transform=get_inference_transforms(image_size),
        base_dir=base_dir,
    )
    test_dataset = CertificateImageDataset(
        manifest_path=test_csv,
        transform=get_inference_transforms(image_size),
        base_dir=base_dir,
    )

    # Class-weighted sampler for train dataset if imbalance exists
    labels = train_dataset.labels
    class_counts = [labels.count(0.0), labels.count(1.0)]
    if 0 not in class_counts:
        weights_per_class = [1.0 / count for count in class_counts]
        sample_weights = [weights_per_class[int(l)] for l in labels]
        sampler = WeightedRandomSampler(
            weights=sample_weights,
            num_samples=len(sample_weights),
            replacement=True,
        )
        shuffle = False
    else:
        sampler = None
        shuffle = True

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        sampler=sampler,
        shuffle=shuffle if sampler is None else False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )

    return train_loader, val_loader, test_loader
