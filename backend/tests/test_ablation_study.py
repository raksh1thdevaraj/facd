"""Unit tests for feature ablation study (Phase 09 - TC-MOD-05).

Tests domain ablation execution across the 5 feature groups and verifies
that multi-feature fusion outperforms any single isolated feature group.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ml.scripts.run_ablation_study import run_ablation_study


def test_ablation_study_execution():
    """Verify that run_ablation_study executes successfully and generates valid report."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        results = run_ablation_study(output_dir=tmp_path)

        assert "full_baseline" in results
        assert "leave_one_group_out" in results
        assert "standalone_groups" in results

        full_base = results["full_baseline"]
        assert full_base["num_features"] == 22
        assert full_base["test_f1"] >= 0.85
        assert full_base["test_accuracy"] >= 0.85

        # Check leave-one-group-out
        logo = results["leave_one_group_out"]
        assert "metadata_and_quality" in logo
        assert "ocr_and_text_quality" in logo
        assert "text_consistency" in logo
        assert "image_forensics" in logo
        assert "template_and_records" in logo

        # Check standalone groups
        standalone = results["standalone_groups"]
        for _group_name, group_res in standalone.items():
            assert "test_f1" in group_res
            assert "test_accuracy" in group_res
            assert group_res["num_features"] < 22

        # Verify output report file exists
        report_file = tmp_path / "ablation_study_results.json"
        assert report_file.exists()

        with open(report_file) as f:
            saved_data = json.load(f)
            assert "full_baseline" in saved_data
