"""Unit tests for CertificateVisualCNN architecture and layer freezing."""

import pytest
import torch
import torch.nn as nn

from app.modules.visual_model.network import CertificateVisualCNN


def test_visual_cnn_forward_shapes():
    """Verify forward pass output dimensions: logits (B,) and embeddings (B, 512)."""
    model = CertificateVisualCNN(
        backbone_name="efficientnet_b0", pretrained=False, embedding_dim=512
    )
    model.eval()

    dummy_input = torch.randn(2, 3, 512, 512)
    with torch.no_grad():
        logits, embeddings = model(dummy_input)

    assert logits.shape == (2,)
    assert embeddings.shape == (2, 512)


def test_visual_cnn_resnet50_option():
    """Verify alternative ResNet50 backbone instantiates and executes."""
    model = CertificateVisualCNN(backbone_name="resnet50", pretrained=False, embedding_dim=512)
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224)
    with torch.no_grad():
        logits, embeddings = model(dummy_input)

    assert logits.shape == (1,)
    assert embeddings.shape == (1, 512)


def test_visual_cnn_invalid_backbone():
    """Verify unsupported backbone raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported backbone"):
        CertificateVisualCNN(backbone_name="vgg16", pretrained=False)


def test_backbone_freeze_and_unfreeze():
    """Verify backbone freezing and unfreezing mechanisms."""
    model = CertificateVisualCNN(backbone_name="efficientnet_b0", pretrained=False)

    # Freeze
    model.freeze_backbone()
    for param in model.backbone.parameters():
        assert param.requires_grad is False
    for param in model.embedding_layer.parameters():
        assert param.requires_grad is True

    # Unfreeze top blocks
    model.unfreeze_backbone(top_blocks_only=True)
    # Check that at least some backbone parameters now require grad
    requires_grad_count = sum(1 for p in model.backbone.parameters() if p.requires_grad)
    assert requires_grad_count > 0


def test_target_conv_layer():
    """Verify target convolutional layer is retrieved for Grad-CAM."""
    model = CertificateVisualCNN(backbone_name="efficientnet_b0", pretrained=False)
    target_layer = model.get_target_conv_layer()
    assert isinstance(target_layer, nn.Module)
