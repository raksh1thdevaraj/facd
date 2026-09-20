"""Early fusion module combining 512D visual embeddings and 22D tabular features."""

from __future__ import annotations

from typing import List, Union

import numpy as np
import torch
from torch import nn


def concatenate_features(
    visual_embedding: np.ndarray,
    tabular_vector: np.ndarray,
) -> np.ndarray:
    """Concatenate 512D visual embedding and 22D tabular vector into 534D representation."""
    v_emb = np.nan_to_num(
        np.asarray(visual_embedding, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0
    )
    t_vec = np.nan_to_num(
        np.asarray(tabular_vector, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0
    )

    if v_emb.ndim == 1 and t_vec.ndim == 1:
        if v_emb.shape[0] != 512 or t_vec.shape[0] != 22:
            raise ValueError(
                f"Expected shapes (512,) and (22,), got {v_emb.shape} and {t_vec.shape}"
            )
        fused = np.concatenate([v_emb, t_vec], axis=0)
        assert fused.shape == (534,)
        return fused
    elif v_emb.ndim == 2 and t_vec.ndim == 2:
        if v_emb.shape[1] != 512 or t_vec.shape[1] != 22:
            raise ValueError(
                f"Expected dims (*, 512) and (*, 22), got {v_emb.shape} and {t_vec.shape}"
            )
        fused = np.concatenate([v_emb, t_vec], axis=1)
        assert fused.shape[1] == 534
        return fused
    else:
        raise ValueError(
            f"Dimension mismatch between visual ({v_emb.ndim}D) and tabular ({t_vec.ndim}D)"
        )


class MultimodalFusionMLP(nn.Module):
    """Deep Multi-Layer Perceptron learning joint cross-modal representations from 534D features."""

    def __init__(
        self,
        input_dim: int = 534,
        hidden_dims: List[int] | None = None,
        dropout_rate: float = 0.3,
    ) -> None:
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [256, 64]

        layers: List[nn.Module] = []
        in_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend(
                [
                    nn.Linear(in_dim, h_dim),
                    nn.BatchNorm1d(h_dim),
                    nn.ReLU(inplace=True),
                    nn.Dropout(dropout_rate),
                ]
            )
            in_dim = h_dim

        layers.append(nn.Linear(in_dim, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass. Expects tensor of shape (B, 534) -> returns logits (B,)."""
        return self.network(x).squeeze(-1)

    def predict_probability(self, features: Union[np.ndarray, torch.Tensor]) -> float:
        """Predict manipulation probability for a single 534D feature vector."""
        self.eval()
        with torch.no_grad():
            if isinstance(features, np.ndarray):
                if features.ndim == 1:
                    features = features[np.newaxis, :]
                tensor = torch.from_numpy(features).float()
            else:
                tensor = features
                if tensor.dim() == 1:
                    tensor = tensor.unsqueeze(0)

            logits = self.forward(tensor)
            prob = torch.sigmoid(logits[0]).item()
            return float(prob)
