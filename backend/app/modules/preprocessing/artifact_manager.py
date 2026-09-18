from pathlib import Path
from typing import Optional, Tuple
from uuid import UUID

import cv2

from app.config import settings
from app.modules.preprocessing.result import PreprocessingResult


class PreprocessingArtifactManager:
    """Manages filesystem persistence of preprocessed images and audit artifacts."""

    def __init__(self, target_dir: Optional[Path] = None):
        self.target_dir = (target_dir or settings.PREPROCESSED_DIR).resolve()
        self.target_dir.mkdir(parents=True, exist_ok=True)

    def save_artifacts(
        self, certificate_id: UUID, result: PreprocessingResult
    ) -> Tuple[Path, Path, Path]:
        """Save enhanced image, binarized image, and thumbnail for a certificate.

        Guarantees that raw files in uploads are untouched.
        """
        prefix = str(certificate_id)

        enhanced_path = self.target_dir / f"{prefix}_enhanced.png"
        binarized_path = self.target_dir / f"{prefix}_binarized.png"
        thumbnail_path = self.target_dir / f"{prefix}_thumbnail.png"

        png_params = [cv2.IMWRITE_PNG_COMPRESSION, 4]

        # 1. Save enhanced color image
        cv2.imwrite(str(enhanced_path), result.enhanced_image, png_params)

        # 2. Save binarized image for OCR
        cv2.imwrite(str(binarized_path), result.binarized_image, png_params)

        # 3. Save thumbnail preview
        thumb = result.thumbnail_image
        if thumb is None:
            from app.modules.preprocessing.resizer import create_thumbnail

            thumb = create_thumbnail(result.enhanced_image, max_edge=400)
        cv2.imwrite(str(thumbnail_path), thumb, png_params)

        result.enhanced_image_path = enhanced_path
        result.binarized_image_path = binarized_path
        result.thumbnail_path = thumbnail_path

        return enhanced_path, binarized_path, thumbnail_path
