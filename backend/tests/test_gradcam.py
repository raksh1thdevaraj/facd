"""Unit tests for GradCAMExplainer (visual heatmaps and overlay generation)."""

from pathlib import Path

import numpy as np
import torch
from PIL import Image

from app.modules.visual_model.gradcam import GradCAMExplainer
from app.modules.visual_model.network import CertificateVisualCNN


def test_gradcam_heatmap_generation():
    """Verify Grad-CAM generates valid heatmap array bounded [0, 1] (TC-DL-04)."""
    model = CertificateVisualCNN(backbone_name="efficientnet_b0", pretrained=False)
    explainer = GradCAMExplainer(model, device="cpu")

    dummy_input = torch.randn(1, 3, 512, 512)
    heatmap = explainer.generate_heatmap(dummy_input)

    assert isinstance(heatmap, np.ndarray)
    assert heatmap.shape == (512, 512)
    assert heatmap.min() >= 0.0
    assert heatmap.max() <= 1.0


def test_gradcam_save_overlay(tmp_path: Path):
    """Verify Grad-CAM overlay image generation and file saving."""
    model = CertificateVisualCNN(backbone_name="efficientnet_b0", pretrained=False)
    explainer = GradCAMExplainer(model, device="cpu")

    # Create dummy image
    test_img_path = tmp_path / "test_cert.png"
    Image.new("RGB", (512, 512), color=(240, 240, 240)).save(test_img_path)

    output_overlay = tmp_path / "overlay.png"
    result_path = explainer.save_overlay(test_img_path, output_overlay)

    assert result_path.exists()
    assert result_path.stat().st_size > 0
