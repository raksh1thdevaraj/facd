"""Unit tests for dataset loading and balanced sampling."""

import torch
from ml.scripts.dataset_loader import CertificateImageDataset, create_dataloaders


def test_certificate_dataset_loading():
    """Verify loading dataset from splits."""
    ds = CertificateImageDataset(
        manifest_path="ml/data/splits/val.csv",
        base_dir=".",
    )
    assert len(ds) > 0
    sample = ds[0]
    assert "image" in sample
    assert "label" in sample
    assert isinstance(sample["image"], torch.Tensor)
    assert sample["image"].shape == (3, 512, 512)
    assert sample["label"].item() in (0.0, 1.0)


def test_create_dataloaders():
    """Verify DataLoaders creation and batch extraction."""
    config = {"image_size": 256, "batch_size": 4, "num_workers": 0}
    train_loader, val_loader, test_loader = create_dataloaders(config, base_dir=".")

    assert len(train_loader) > 0
    assert len(val_loader) > 0
    assert len(test_loader) > 0

    batch = next(iter(train_loader))
    assert batch["image"].shape == (4, 3, 256, 256)
    assert batch["label"].shape == (4,)

    val_batch = next(iter(val_loader))
    assert val_batch["image"].shape[1:] == (3, 256, 256)
