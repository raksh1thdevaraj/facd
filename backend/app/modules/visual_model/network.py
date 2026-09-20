"""Neural network architecture for certificate visual tampering detection."""

from __future__ import annotations

import logging
from typing import Tuple

import torch
import torch.nn as nn
from torchvision import models

logger = logging.getLogger(__name__)


class CertificateVisualCNN(nn.Module):
    """Convolutional Neural Network for certificate visual manipulation classification.

    Extracts a 512-dimensional visual embedding vector from the penultimate layer and
    outputs a single binary logit for tampering probability.
    """

    def __init__(
        self,
        backbone_name: str = "efficientnet_b0",
        pretrained: bool = True,
        embedding_dim: int = 512,
    ) -> None:
        super().__init__()
        self.backbone_name = backbone_name
        self.embedding_dim = embedding_dim

        if backbone_name == "efficientnet_b0":
            try:
                weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
                base_model = models.efficientnet_b0(weights=weights)
            except Exception as e:
                logger.warning(
                    "Failed to fetch pretrained weights for efficientnet_b0: %s. Using unweighted.",
                    e,
                )
                base_model = models.efficientnet_b0(weights=None)

            in_features = base_model.classifier[1].in_features  # 1280
            base_model.classifier = nn.Identity()
            self.backbone = base_model
            self._target_conv = self.backbone.features[-1]
        elif backbone_name == "resnet50":
            try:
                weights = models.ResNet50_Weights.DEFAULT if pretrained else None
                base_model = models.resnet50(weights=weights)
            except Exception as e:
                logger.warning(
                    "Failed to fetch pretrained weights for resnet50: %s. Using unweighted.", e
                )
                base_model = models.resnet50(weights=None)

            in_features = base_model.fc.in_features  # 2048
            base_model.fc = nn.Identity()
            self.backbone = base_model
            self._target_conv = self.backbone.layer4[-1]
        else:
            raise ValueError(
                f"Unsupported backbone: {backbone_name}. Choose 'efficientnet_b0' or 'resnet50'."
            )

        # Visual embedding projection layer (512-dim)
        self.embedding_layer = nn.Sequential(
            nn.Linear(in_features, embedding_dim),
            nn.BatchNorm1d(embedding_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.3),
        )

        # Binary classification output head (logits)
        self.classifier = nn.Linear(embedding_dim, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Forward pass.

        Args:
            x: Input image tensor of shape (B, 3, H, W)

        Returns:
            logits: Shape (B,)
            embeddings: Shape (B, embedding_dim)
        """
        features = self.backbone(x)  # (B, in_features)
        embeddings = self.embedding_layer(features)  # (B, 512)
        logits = self.classifier(embeddings).squeeze(-1)  # (B,)
        return logits, embeddings

    def freeze_backbone(self) -> None:
        """Freeze all parameters in the convolutional backbone for Stage 1 fine-tuning."""
        for param in self.backbone.parameters():
            param.requires_grad = False

    def unfreeze_backbone(self, top_blocks_only: bool = False) -> None:
        """Unfreeze backbone parameters for Stage 2 fine-tuning.

        Args:
            top_blocks_only: If True, only unfreezes top-level blocks.
        """
        if not top_blocks_only:
            for param in self.backbone.parameters():
                param.requires_grad = True
            return

        if self.backbone_name == "efficientnet_b0":
            # Unfreeze only the last 3 stages of features
            for i, block in enumerate(self.backbone.features):
                requires = i >= 6
                for param in block.parameters():
                    param.requires_grad = requires
        elif self.backbone_name == "resnet50":
            # Unfreeze only layer4
            for param in self.backbone.parameters():
                param.requires_grad = False
            for param in self.backbone.layer4.parameters():
                param.requires_grad = True

    def get_target_conv_layer(self) -> nn.Module:
        """Return the final convolutional layer of the backbone for Grad-CAM."""
        return self._target_conv
