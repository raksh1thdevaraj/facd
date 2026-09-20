import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.config import settings
from app.models.template import InstitutionTemplateModel


def load_precomputed_template_features(
    feature_path: str,
) -> Optional[Tuple[np.ndarray, np.ndarray]]:
    """Load pre-computed keypoints coordinates and descriptors from compressed npz archive."""
    p = Path(feature_path)
    if not p.exists():
        return None
    try:
        data = np.load(str(p))
        pts = data["pts"]
        des = data["descriptors"]
        return pts, des
    except Exception:
        return None


def register_institution_template(
    template_img: np.ndarray,
    institution_id: str,
    template_name: str,
    db: Session,
    degree_program: Optional[str] = None,
    effective_year_start: Optional[int] = None,
    effective_year_end: Optional[int] = None,
    seal_roi: Optional[Dict[str, Any]] = None,
    variable_regions: Optional[List[Dict[str, Any]]] = None,
) -> InstitutionTemplateModel:
    """Register and index master template, persisting image and precomputed features.

    Args:
        template_img: Master template RGB or grayscale image array.
        institution_id: UUID of issuing academic institution.
        template_name: Distinct name for template layout (e.g. "B.Tech Degree 2020-2024").
        db: SQLAlchemy database session.
        degree_program: Specific academic program associated with template.
        effective_year_start: Start year template was utilized.
        effective_year_end: End year template was utilized.
        seal_roi: Bounding box dictionary {x, y, width, height} of official seal.
        variable_regions: List of bounding box dicts for variable student text to mask.

    Returns:
        Persisted InstitutionTemplateModel.
    """
    settings.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    template_id = str(uuid.uuid4())

    # 1. Save master template image to disk
    image_filename = f"{institution_id}_{template_id}.png"
    image_path = settings.TEMPLATES_DIR / image_filename
    cv2.imwrite(str(image_path), template_img)

    # 2. Precompute and persist ORB feature descriptors
    gray = (
        cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY) if template_img.ndim == 3 else template_img
    )
    orb = cv2.ORB_create(nfeatures=2000)
    keypoints, descriptors = orb.detectAndCompute(gray, None)

    pts = (
        np.array([kp.pt for kp in keypoints], dtype=np.float32)
        if keypoints
        else np.empty((0, 2), dtype=np.float32)
    )
    des_array = descriptors if descriptors is not None else np.empty((0, 32), dtype=np.uint8)

    feature_filename = f"{institution_id}_{template_id}_features.npz"
    feature_path = settings.TEMPLATES_DIR / feature_filename
    np.savez_compressed(str(feature_path), pts=pts, descriptors=des_array)

    # 3. Create database record
    new_template = InstitutionTemplateModel(
        id=template_id,
        institution_id=institution_id,
        template_name=template_name,
        degree_program=degree_program,
        effective_year_start=effective_year_start,
        effective_year_end=effective_year_end,
        image_path=str(image_path),
        feature_data_path=str(feature_path),
        seal_roi_json=seal_roi or {},
        variable_regions_json=variable_regions or [],
    )

    db.add(new_template)
    db.commit()
    db.refresh(new_template)

    return new_template
