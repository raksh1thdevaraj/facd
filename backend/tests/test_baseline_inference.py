"""Unit tests for baseline inference engine (Phase 09 - TC-MOD-04).

Tests inference latency benchmark (< 50ms over 100 iterations),
batch inference consistency, error handling, and fallback behavior.
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from app.modules.ml_classifier.inference_engine import BaselineInferenceEngine


@pytest.fixture
def inference_engine():
    """Returns BaselineInferenceEngine pointing to default serialized model."""
    engine = BaselineInferenceEngine()
    return engine


def test_inference_latency_benchmark(inference_engine):
    """Verify single certificate inference latency is under 50ms over 100 runs (TC-MOD-04)."""
    sample = np.random.uniform(0.0, 1.0, size=22).astype(np.float32)

    # Warm-up run
    inference_engine.predict_single(sample)

    latencies = []
    for _ in range(100):
        start = time.perf_counter()
        prob, pred_class, conf, measured_ms = inference_engine.predict_single(sample)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        latencies.append(elapsed_ms)

        assert 0.0 <= prob <= 1.0
        assert pred_class in ["authentic", "manipulated"]
        assert 0.0 <= conf <= 1.0

    mean_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)

    # Must be well below 50ms (typically < 5ms for RandomForest/LogReg)
    assert mean_latency < 50.0, f"Mean latency {mean_latency:.2f}ms exceeds 50ms"
    assert p95_latency < 50.0, f"P95 latency {p95_latency:.2f}ms exceeds 50ms"


def test_batch_inference_consistency(inference_engine):
    """Verify batch inference matches individual single predictions."""
    batch = np.random.uniform(0.0, 1.0, size=(10, 22)).astype(np.float32)

    batch_results = inference_engine.predict_batch(batch)
    assert len(batch_results) == 10

    for i, row in enumerate(batch):
        single_prob, single_class, single_conf, _ = inference_engine.predict_single(row)
        batch_prob, batch_class, batch_conf = batch_results[i]

        assert pytest.approx(single_prob, abs=1e-4) == batch_prob
        assert single_class == batch_class
        assert pytest.approx(single_conf, abs=1e-4) == batch_conf


def test_invalid_dimension_raises_error(inference_engine):
    """Verify inference engine raises ValueError on invalid feature vector size."""
    with pytest.raises(ValueError, match="Expected 22 features"):
        inference_engine.predict_single(np.zeros(21))

    with pytest.raises(ValueError, match="Expected array of shape"):
        inference_engine.predict_batch(np.zeros((5, 10)))


def test_fallback_heuristic_when_model_missing():
    """Verify graceful fallback heuristic when model artifact cannot be found."""
    engine = BaselineInferenceEngine(model_path="/non/existent/path/model.joblib")
    assert not engine.is_ready()

    sample = np.zeros(22, dtype=np.float32)
    # Set forensic scores to indicate anomaly
    sample[13] = 0.9  # ela_score
    sample[14] = 0.8  # copy_move_score
    sample[16] = 0.85  # noise_inconsistency_score

    prob, pred_class, conf, latency_ms = engine.predict_single(sample)

    assert 0.0 <= prob <= 1.0
    assert pred_class in ["authentic", "manipulated"]
    assert latency_ms >= 0.0
