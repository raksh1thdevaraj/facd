"""Image transformation and normalization pipelines for certificate visual classification."""

from __future__ import annotations

import numpy as np
import torch
from torchvision import transforms

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def get_train_transforms(image_size: int = 512) -> transforms.Compose:
    """Document-safe augmentation pipeline for training."""
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.RandomRotation(degrees=(-5, 5), fill=255),
            transforms.ColorJitter(brightness=0.15, contrast=0.2, saturation=0.1, hue=0.05),
            transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.0)),
            transforms.ToTensor(),
            transforms.RandomErasing(p=0.2, scale=(0.02, 0.1), ratio=(0.5, 2.0), value=1.0),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def get_inference_transforms(image_size: int = 512) -> transforms.Compose:
    """Strictly deterministic transformation pipeline for validation and production inference."""
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def denormalize_image(tensor: torch.Tensor) -> np.ndarray:
    """Convert normalized PyTorch tensor (3, H, W) back to uint8 RGB numpy array (H, W, 3)."""
    img = tensor.detach().cpu().clone().numpy()
    if img.ndim == 4:
        img = img[0]
    for c, (m, s) in enumerate(zip(IMAGENET_MEAN, IMAGENET_STD, strict=True)):
        img[c] = img[c] * s + m
    img = np.clip(img * 255.0, 0, 255).astype(np.uint8)
    return np.transpose(img, (1, 2, 0))
