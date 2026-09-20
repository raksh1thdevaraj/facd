"""Grad-CAM (Gradient-weighted Class Activation Mapping) for visual explainability."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from app.modules.visual_model.network import CertificateVisualCNN
from app.modules.visual_model.transforms import get_inference_transforms


class GradCAMExplainer:
    """Computes Grad-CAM heatmaps highlighting visual regions indicative of tampering."""

    def __init__(
        self, model: CertificateVisualCNN, device: Union[torch.device, str] = "cpu"
    ) -> None:
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        self.transforms = get_inference_transforms()

        self._target_layer = self.model.get_target_conv_layer()
        self._activations: Optional[torch.Tensor] = None
        self._gradients: Optional[torch.Tensor] = None
        self._register_hooks()

    def _register_hooks(self) -> None:
        def forward_hook(module, input, output):
            self._activations = output

        def backward_hook(module, grad_input, grad_output):
            self._gradients = grad_output[0]

        self._target_layer.register_forward_hook(forward_hook)
        self._target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(self, image_tensor: torch.Tensor) -> np.ndarray:
        """Compute Grad-CAM heatmap array of shape (H, W) normalized to [0.0, 1.0]."""
        self.model.eval()
        if image_tensor.dim() == 3:
            image_tensor = image_tensor.unsqueeze(0)

        image_tensor = image_tensor.to(self.device)
        image_tensor.requires_grad_(True)

        self.model.zero_grad()
        logits, _ = self.model(image_tensor)

        score = logits[0]
        score.backward(retain_graph=False)

        if self._activations is None or self._gradients is None:
            raise RuntimeError("Grad-CAM hooks failed to capture activations or gradients.")

        # Pooled gradients across spatial dimensions: (B, C, 1, 1)
        weights = torch.mean(self._gradients, dim=(2, 3), keepdim=True)
        # Weighted combination: (B, C, H, W) -> sum -> (B, 1, H, W)
        cam = torch.sum(weights * self._activations, dim=1, keepdim=True)
        cam = F.relu(cam)

        # Upsample to input tensor resolution
        _, _, h, w = image_tensor.shape
        cam = F.interpolate(cam, size=(h, w), mode="bilinear", align_corners=False)

        cam = cam.squeeze().detach().cpu().numpy()
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam)

        return cam.astype(np.float32)

    def generate_overlay(self, image_bgr: np.ndarray, heatmap: np.ndarray) -> np.ndarray:
        """Blend computed heatmap with the raw BGR certificate image."""
        h, w = image_bgr.shape[:2]
        heatmap_resized = cv2.resize(heatmap, (w, h))
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        colored_cam = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        overlay = cv2.addWeighted(image_bgr, 0.65, colored_cam, 0.35, 0)
        return overlay

    def save_overlay(
        self,
        image_path: Union[str, Path],
        output_path: Union[str, Path],
        tensor: Optional[torch.Tensor] = None,
    ) -> Path:
        """Compute Grad-CAM for image file and save visual overlay to output_path."""
        image_path = Path(image_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if tensor is None:
            with Image.open(image_path) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                tensor = self.transforms(img)

        heatmap = self.generate_heatmap(tensor)
        raw_bgr = cv2.imread(str(image_path))
        if raw_bgr is None:
            # Fallback if cv2 cannot read: convert tensor to BGR
            with Image.open(image_path) as img:
                raw_bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        overlay = self.generate_overlay(raw_bgr, heatmap)
        cv2.imwrite(str(output_path), overlay)
        return output_path
