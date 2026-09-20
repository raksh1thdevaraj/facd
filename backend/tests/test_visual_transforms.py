"""Unit tests for visual transformation and normalization pipelines."""

import numpy as np
import torch
from PIL import Image

from app.modules.visual_model.transforms import (
    denormalize_image,
    get_inference_transforms,
    get_train_transforms,
)


def test_train_transforms():
    """Verify training transforms produce normalized (3, 512, 512) tensor."""
    img = Image.new("RGB", (600, 800), color=(240, 240, 240))
    t = get_train_transforms(image_size=512)
    tensor = t(img)

    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (3, 512, 512)
    assert tensor.dtype == torch.float32


def test_inference_transforms():
    """Verify deterministic inference transforms produce correct tensor shape and values."""
    img = Image.new("RGB", (400, 300), color=(128, 128, 128))
    t = get_inference_transforms(image_size=512)
    tensor = t(img)

    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (3, 512, 512)
    assert not torch.isnan(tensor).any()


def test_denormalize_image():
    """Verify denormalization returns uint8 numpy image in [0, 255]."""
    dummy_tensor = torch.zeros(3, 256, 256)
    img_np = denormalize_image(dummy_tensor)

    assert isinstance(img_np, np.ndarray)
    assert img_np.shape == (256, 256, 3)
    assert img_np.dtype == np.uint8
    assert img_np.min() >= 0
    assert img_np.max() <= 255
