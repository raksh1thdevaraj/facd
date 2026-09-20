"""Unit tests for Early Fusion feature concatenation and Multimodal MLP."""

import numpy as np
import pytest
import torch

from app.modules.score_fusion.early_fusion import (
    MultimodalFusionMLP,
    concatenate_features,
)


def test_feature_concatenation_1d():
    """Verify 1D concatenation of 512D visual and 22D tabular vectors into 534D."""
    v_emb = np.random.randn(512).astype(np.float32)
    t_vec = np.random.randn(22).astype(np.float32)

    fused = concatenate_features(v_emb, t_vec)
    assert isinstance(fused, np.ndarray)
    assert fused.shape == (534,)
    assert fused.dtype == np.float32


def test_feature_concatenation_2d():
    """Verify 2D batch concatenation."""
    v_emb = np.random.randn(4, 512).astype(np.float32)
    t_vec = np.random.randn(4, 22).astype(np.float32)

    fused = concatenate_features(v_emb, t_vec)
    assert fused.shape == (4, 534)


def test_feature_concatenation_invalid_dim():
    """Verify ValueError is raised on mismatched input dimensions."""
    v_emb = np.random.randn(500)
    t_vec = np.random.randn(22)
    with pytest.raises(ValueError):
        concatenate_features(v_emb, t_vec)


def test_early_fusion_mlp_forward_and_predict():
    """Verify MultimodalFusionMLP forward pass and probability prediction."""
    model = MultimodalFusionMLP(input_dim=534, hidden_dims=[128, 32])
    model.eval()

    dummy_batch = torch.randn(2, 534)
    with torch.no_grad():
        logits = model(dummy_batch)
    assert logits.shape == (2,)

    # Test single vector probability prediction
    single_vector = np.random.randn(534).astype(np.float32)
    prob = model.predict_probability(single_vector)
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0
