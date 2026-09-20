"""Unit tests for VisualEmbeddingExtractor (512D normalized visual vectors)."""

import numpy as np
import torch
from PIL import Image

from app.modules.visual_model.embedding_extractor import VisualEmbeddingExtractor
from app.modules.visual_model.network import CertificateVisualCNN


def test_visual_embedding_extraction():
    """Verify extracted embedding is 512-dim with L2 norm equal to 1.0 (TC-DL-03)."""
    model = CertificateVisualCNN(
        backbone_name="efficientnet_b0", pretrained=False, embedding_dim=512
    )
    extractor = VisualEmbeddingExtractor(model, device="cpu")

    dummy_tensor = torch.randn(1, 3, 512, 512)
    embedding = extractor.extract(dummy_tensor)

    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (512,)
    assert embedding.dtype == np.float32

    # L2 Norm should be exactly 1.0 within numerical precision
    norm = float(np.linalg.norm(embedding))
    assert abs(norm - 1.0) < 1e-4


def test_visual_embedding_from_pil():
    """Verify extraction directly from PIL Image."""
    model = CertificateVisualCNN(backbone_name="efficientnet_b0", pretrained=False)
    extractor = VisualEmbeddingExtractor(model, device="cpu")

    img = Image.new("RGB", (256, 256), color=(200, 200, 200))
    embedding = extractor.extract_from_pil(img)

    assert embedding.shape == (512,)
    norm = float(np.linalg.norm(embedding))
    assert abs(norm - 1.0) < 1e-4
