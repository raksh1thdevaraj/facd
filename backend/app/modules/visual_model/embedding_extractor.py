"""Visual feature embedding extractor for multimodal fusion."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from app.modules.visual_model.network import CertificateVisualCNN
from app.modules.visual_model.transforms import get_inference_transforms


class VisualEmbeddingExtractor:
    """Extracts 512-dimensional L2-normalized visual feature embeddings from penultimate layer."""

    def __init__(
        self, model: CertificateVisualCNN, device: Union[torch.device, str] = "cpu"
    ) -> None:
        self.model = model
        self.device = torch.device(device)
        self.model.to(self.device)
        self.transforms = get_inference_transforms()

    def extract(self, image_tensor: torch.Tensor) -> np.ndarray:
        """Extract normalized 512D embedding from tensor of shape (1, 3, H, W) or (3, H, W)."""
        self.model.eval()
        with torch.no_grad():
            if image_tensor.dim() == 3:
                image_tensor = image_tensor.unsqueeze(0)
            image_tensor = image_tensor.to(self.device)
            _, embedding = self.model(image_tensor)
            normalized = F.normalize(embedding, p=2, dim=1)
            return normalized.cpu().numpy().squeeze(0).astype(np.float32)

    def extract_from_pil(self, image: Image.Image) -> np.ndarray:
        """Extract normalized 512D embedding from PIL Image."""
        if image.mode != "RGB":
            image = image.convert("RGB")
        tensor = self.transforms(image)
        return self.extract(tensor)

    def extract_from_path(self, image_path: Union[str, Path]) -> np.ndarray:
        """Extract normalized 512D embedding directly from image file path."""
        with Image.open(image_path) as img:
            return self.extract_from_pil(img)
