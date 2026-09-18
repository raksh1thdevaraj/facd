from pathlib import Path

import cv2
import numpy as np
import pytest
from ml.scripts.generate_genuine import generate_synthetic_record, render_genuine_certificate
from ml.scripts.generate_manipulated import (
    apply_recompression_discrepancy,
    copy_move_tampering,
    inpaint_and_replace_text,
)
from ml.scripts.generate_templates import generate_all_templates
from ml.scripts.split_dataset import create_dataset_splits
from PIL import Image


@pytest.fixture(scope="module")
def generated_templates(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate temporary base templates fixture."""
    test_dir = tmp_path_factory.mktemp("test_dataset_dir")
    generate_all_templates(test_dir)
    return test_dir


def test_template_generation(generated_templates: Path) -> None:
    """Verify templates and asset files are properly generated."""
    raw_dir = generated_templates / "raw"
    assert (raw_dir / "templates_meta.json").exists()
    assert (raw_dir / "template_tech_univ.png").exists()
    assert (generated_templates / "assets" / "seals" / "seal_tech.png").exists()
    assert (generated_templates / "assets" / "signatures" / "sig_registrar.png").exists()


def test_genuine_certificate_rendering(generated_templates: Path) -> None:
    """Verify genuine certificate rendering and bounding box calculation."""
    raw_dir = generated_templates / "raw"
    assets_dir = generated_templates / "assets"

    import json

    with open(raw_dir / "templates_meta.json", "r", encoding="utf-8") as f:
        meta = json.load(f)["templates"][0]

    record = generate_synthetic_record()
    img, field_boxes = render_genuine_certificate(meta, record, raw_dir, assets_dir)

    assert isinstance(img, Image.Image)
    assert img.size == (1920, 1350)
    assert "student_name" in field_boxes
    assert "grade_or_marks" in field_boxes

    # Verify normalized bounding box ranges
    for _field, box_info in field_boxes.items():
        n_box = box_info["bbox_normalized"]
        assert 0.0 <= n_box["x1"] < n_box["x2"] <= 1.0
        assert 0.0 <= n_box["y1"] < n_box["y2"] <= 1.0


def test_inpaint_and_replace_tampering() -> None:
    """Verify text inpainting and replacement modification."""
    # Create test canvas
    canvas = np.full((300, 400, 3), 240, dtype=np.uint8)
    cv2.putText(canvas, "ORIGINAL 3.50", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

    box = {"x": 40, "y": 120, "width": 250, "height": 50}
    tampered, info = inpaint_and_replace_text(canvas, box, "ALTERED 4.00", font_mismatched=True)

    assert tampered.shape == canvas.shape
    assert info["technique"] == "INPAINT_AND_REPLACE"
    assert info["font_mismatched"] is True
    assert 0.0 <= info["bbox_normalized"]["x1"] < info["bbox_normalized"]["x2"] <= 1.0


def test_copy_move_tampering() -> None:
    """Verify copy-move duplication operator."""
    canvas = np.full((300, 400, 3), 240, dtype=np.uint8)
    cv2.circle(canvas, (100, 150), 30, (10, 10, 10), -1)

    source_box = {"x": 70, "y": 120, "width": 60, "height": 60}
    tampered, info = copy_move_tampering(canvas, source_box, target_x=220, target_y=120)

    assert info["technique"] == "COPY_MOVE"
    assert info["bbox_pixel"]["x"] == 220


def test_recompression_discrepancy() -> None:
    """Verify localized JPEG quality degradation operator."""
    canvas = np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)
    box = {"x": 50, "y": 50, "width": 100, "height": 100}
    tampered, info = apply_recompression_discrepancy(canvas, box, low_q=50)

    assert info["technique"] == "RECOMPRESSION_DISCREPANCY"
    assert info["quality_factor"] == 50


def test_dataset_splits_and_manifests(tmp_path: Path) -> None:
    """Verify train/val/test splitting and manifest generation."""
    samples = []
    for i in range(20):
        is_manip = i % 2 == 1
        samples.append(
            {
                "sample_id": f"SAMPLE_{i:04d}",
                "image_path": f"datasets/synthetic_manipulated/img_{i}.png",
                "is_manipulated": is_manip,
                "primary_label": "manipulated" if is_manip else "genuine",
                "manipulation_types": ["TEXT_REPLACEMENT"] if is_manip else [],
                "source_template": "template_tech_univ.png",
                "source_template_id": (
                    "template_tech_univ" if i < 16 else "template_national_academy"
                ),
                "base_resolution": [1920, 1350],
            }
        )

    splits = create_dataset_splits(samples, tmp_path)

    assert "train" in splits
    assert "val" in splits
    assert "test" in splits

    gt_dir = tmp_path / "ground_truth"
    assert (gt_dir / "train_manifest.json").exists()
    assert (gt_dir / "val_manifest.json").exists()
    assert (gt_dir / "test_manifest.json").exists()
    assert (tmp_path / "splits" / "train.csv").exists()
