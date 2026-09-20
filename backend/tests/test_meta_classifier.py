"""Unit tests for StackingMetaClassifier."""

from pathlib import Path

import numpy as np
import pytest

from app.modules.score_fusion.meta_classifier import StackingMetaClassifier


def test_meta_classifier_predict_default():
    """Verify meta-classifier predicts bounded probability on 5D vector."""
    clf = StackingMetaClassifier()
    # Features: [visual_fake, tabular_fake, forensic, text, template]
    authentic_feats = [0.05, 0.05, 0.95, 0.95, 0.90]
    p_auth = clf.predict_authenticity(authentic_feats)
    assert 0.0 <= p_auth <= 1.0
    assert p_auth > 0.50

    fake_feats = [0.90, 0.95, 0.10, 0.15, 0.20]
    p_fake = clf.predict_authenticity(fake_feats)
    assert p_fake < 0.50


def test_meta_classifier_fit_and_save(tmp_path: Path):
    """Verify fitting meta-classifier and saving/loading artifact."""
    X = np.array(
        [
            [0.1, 0.1, 0.9, 0.9, 0.9],
            [0.9, 0.9, 0.1, 0.1, 0.1],
            [0.2, 0.1, 0.8, 0.8, 0.9],
            [0.8, 0.8, 0.2, 0.3, 0.1],
        ],
        dtype=np.float32,
    )
    y = np.array([1, 0, 1, 0], dtype=np.int32)

    clf = StackingMetaClassifier()
    clf.fit(X, y)

    model_file = tmp_path / "meta_model.joblib"
    clf.save(model_file)
    assert model_file.exists()

    loaded_clf = StackingMetaClassifier(model_path=model_file)
    p = loaded_clf.predict_authenticity([0.1, 0.1, 0.9, 0.9, 0.9])
    assert p > 0.50


def test_meta_classifier_invalid_features():
    """Verify error on incorrect feature count."""
    clf = StackingMetaClassifier()
    with pytest.raises(ValueError):
        clf.predict_authenticity([0.1, 0.2, 0.3])
