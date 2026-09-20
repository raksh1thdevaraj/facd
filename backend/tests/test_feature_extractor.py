"""Unit tests for TabularFeatureExtractor (Phase 09).

Tests 22-dimensional feature extraction, robust fallback imputation,
bounds enforcement, and upstream module integration.
"""

from __future__ import annotations

import numpy as np

from app.modules.ml_classifier.feature_extractor import TabularFeatureExtractor
from app.schemas.ml_prediction import FEATURE_NAMES, FeatureVector


def test_feature_names_count():
    """Verify that authoritative feature list defines exactly 22 features."""
    assert len(FEATURE_NAMES) == 22
    assert "file_size_kb" in FEATURE_NAMES
    assert "ela_score" in FEATURE_NAMES
    assert "record_match_score" in FEATURE_NAMES


def test_extract_from_upstream_empty_fallbacks():
    """Verify feature extractor populates 22 features when inputs are None."""
    extractor = TabularFeatureExtractor()
    feat_vector = extractor.extract_from_upstream(
        ingestion_data=None,
        ocr_result=None,
        text_consistency_result=None,
        forensics_result=None,
        template_result=None,
    )

    assert isinstance(feat_vector, FeatureVector)
    feat_dict = feat_vector.to_dict()
    assert len(feat_dict) == 22

    # Check fallbacks
    assert feat_vector.file_size_kb == 500.0
    assert feat_vector.has_exif == 0.0
    assert feat_vector.ocr_mean_confidence == 0.85
    assert feat_vector.ela_score == 0.90
    assert feat_vector.record_found_flag == 0.0

    arr = feat_vector.to_array()
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (22,)
    assert not np.isnan(arr).any()


def test_extract_from_upstream_populated_schemas():
    """Verify feature extractor properly maps fields from mock upstream pipeline outputs."""
    extractor = TabularFeatureExtractor()

    mock_ingestion = {
        "file_size_kb": 1540.5,
        "metadata": {"has_exif": True, "software": "Adobe Photoshop"},
        "quality_metrics": {"aspect_ratio_deviation": 0.02},
    }
    mock_ocr = {
        "mean_confidence": 0.94,
        "min_confidence": 0.81,
        "flagged_fields": ["student_name"],
        "missing_critical_fields": [],
    }
    mock_text = {
        "metrics": {
            "baseline_alignment_score": 0.96,
            "font_size_consistency_score": 0.92,
            "stroke_weight_score": 0.89,
            "character_spacing_score": 0.91,
            "logical_consistency_score": 0.98,
        }
    }
    mock_forensics = {
        "ela_score": 0.85,
        "copy_move_score": 0.94,
        "cloned_regions_count": 0,
        "noise_inconsistency_score": 0.88,
    }
    mock_template = {
        "ssim_score": 0.92,
        "feature_match_score": 0.87,
        "seal_match_score": 0.95,
        "record_found": True,
        "record_match_score": 1.0,
    }

    feat_vector = extractor.extract_from_upstream(
        ingestion_data=mock_ingestion,
        ocr_result=mock_ocr,
        text_consistency_result=mock_text,
        forensics_result=mock_forensics,
        template_result=mock_template,
    )

    assert feat_vector.file_size_kb == 1540.5
    assert feat_vector.has_exif == 1.0
    assert feat_vector.software_editing_flag == 1.0
    assert feat_vector.aspect_ratio_deviation == 0.02
    assert feat_vector.ocr_mean_confidence == 0.94
    assert feat_vector.ocr_min_confidence == 0.81
    assert feat_vector.flagged_field_count == 1.0
    assert feat_vector.missing_critical_fields_count == 0.0
    assert feat_vector.baseline_alignment_score == 0.96
    assert feat_vector.ela_score == 0.85
    assert feat_vector.record_found_flag == 1.0
    assert feat_vector.record_match_score == 1.0

    arr = feat_vector.to_array()
    assert arr.shape == (22,)
    assert arr[0] == 1540.5
    assert arr[20] == 1.0  # record_found_flag
    assert arr[21] == 1.0  # record_match_score


def test_feature_vector_clipping():
    """Verify that score features are clamped between 0.0 and 1.0."""
    extractor = TabularFeatureExtractor()
    mock_text = {
        "metrics": {
            "baseline_alignment_score": 1.5,  # Exceeds max
            "font_size_consistency_score": -0.2,  # Sub-zero
        }
    }
    feat_vector = extractor.extract_from_upstream(text_consistency_result=mock_text)
    assert feat_vector.baseline_alignment_score == 1.0
    assert feat_vector.font_size_consistency_score == 0.0
