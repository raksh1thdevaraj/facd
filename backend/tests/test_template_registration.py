import uuid
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session

from app.modules.template_matching.registration_service import (
    load_precomputed_template_features,
    register_institution_template,
)


def test_tc_tmp_06_template_registration_and_feature_caching(db_session: Session):
    """TC-TMP-06: Register master template, save image, pre-compute features, and store in DB."""
    inst_id = str(uuid.uuid4())
    img = np.ones((600, 800, 3), dtype=np.uint8) * 240
    # Add distinct patterns
    img[50:100, 50:100] = [0, 0, 255]
    img[200:300, 200:300] = [0, 255, 0]

    template = register_institution_template(
        template_img=img,
        institution_id=inst_id,
        template_name="B.Sc Standard Template 2024",
        db=db_session,
        degree_program="Bachelor of Science",
        effective_year_start=2020,
        effective_year_end=2025,
        seal_roi={"x": 50, "y": 50, "width": 50, "height": 50},
        variable_regions=[{"x": 100, "y": 200, "width": 300, "height": 40}],
    )

    assert template.id is not None
    assert template.institution_id == inst_id
    assert template.template_name == "B.Sc Standard Template 2024"

    # Verify image was persisted to disk
    assert Path(template.image_path).exists()

    # Verify feature descriptors were precomputed and cached as .npz
    assert Path(template.feature_data_path).exists()

    # Verify loading cached features
    loaded = load_precomputed_template_features(template.feature_data_path)
    assert loaded is not None
    pts, descriptors = loaded
    assert len(pts) > 0
    assert descriptors.shape[1] == 32  # ORB descriptor length
