import logging
import time
from pathlib import Path
from typing import Optional
from uuid import UUID

import cv2

from app.core.exceptions import InvalidFileError
from app.modules.preprocessing.artifact_manager import PreprocessingArtifactManager
from app.modules.preprocessing.binarizer import AdaptiveBinarizer
from app.modules.preprocessing.contrast_enhancer import CLAHEEnhancer
from app.modules.preprocessing.deskewer import Deskewer
from app.modules.preprocessing.noise_reduction import NoiseReductionFilter
from app.modules.preprocessing.perspective_warper import PerspectiveWarper
from app.modules.preprocessing.pipeline import PreprocessingPipeline
from app.modules.preprocessing.resizer import create_thumbnail, normalize_resolution
from app.modules.preprocessing.result import PreprocessingResult
from app.schemas.preprocessing import PreprocessingConfig

logger = logging.getLogger(__name__)


class PreprocessingService:
    """Orchestrates image preprocessing, resolution normalization,
    binarization, and artifact storage.
    """

    def __init__(
        self,
        artifact_manager: Optional[PreprocessingArtifactManager] = None,
        config: Optional[PreprocessingConfig] = None,
    ):
        self.artifact_manager = artifact_manager or PreprocessingArtifactManager()
        self.config = config or PreprocessingConfig()
        self.pipeline = self._build_pipeline(self.config)

    def _build_pipeline(self, config: PreprocessingConfig) -> PreprocessingPipeline:
        """Construct the sequence of image transformation steps."""
        pipeline = PreprocessingPipeline()

        # Step 1: Perspective boundary rectification
        pipeline.add_step(
            PerspectiveWarper(
                enabled=config.perspective_enabled,
                min_area_ratio=config.min_document_area_ratio,
            )
        )

        # Step 2: Rotational skew correction
        pipeline.add_step(
            Deskewer(
                enabled=config.deskew_enabled,
                max_angle=config.max_deskew_angle,
                min_threshold=config.min_angle_threshold,
            )
        )

        # Step 3: Edge-preserving noise reduction
        pipeline.add_step(
            NoiseReductionFilter(
                filter_type=config.noise_filter,
                d=config.bilateral_d,
                sigma_color=config.bilateral_sigma_color,
                sigma_space=config.bilateral_sigma_space,
            )
        )

        # Step 4: CLAHE illumination and contrast enhancement
        pipeline.add_step(
            CLAHEEnhancer(
                clip_limit=config.clahe_clip_limit,
                tile_grid_size=config.clahe_tile_grid_size,
                enabled=config.contrast_enhancement_enabled,
            )
        )

        return pipeline

    def preprocess(self, certificate_id: UUID, image_path: Path) -> PreprocessingResult:
        """Execute end-to-end preprocessing on an input certificate image.

        Saves derived enhanced, binarized, and thumbnail images to storage/preprocessed.
        The input file at image_path is guaranteed to remain untouched.
        """
        start_time = time.perf_counter()

        if not image_path.exists():
            raise InvalidFileError(f"Source image file does not exist: {image_path}")

        # Read image using OpenCV
        raw_img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if raw_img is None:
            raise InvalidFileError(f"OpenCV failed to decode image at: {image_path}")

        orig_h, orig_w = raw_img.shape[:2]
        context = {
            "certificate_id": str(certificate_id),
            "original_width": orig_w,
            "original_height": orig_h,
        }

        # Execute primary pipeline (perspective -> deskew -> noise -> CLAHE)
        enhanced_img, context = self.pipeline.run(raw_img, context)

        # Normalize resolution while strictly preserving aspect ratio
        enhanced_img, _ = normalize_resolution(
            enhanced_img,
            min_long_edge=self.config.min_long_edge,
            max_long_edge=self.config.max_long_edge,
        )
        proc_h, proc_w = enhanced_img.shape[:2]

        # Generate binarized image optimized for OCR
        binarizer = AdaptiveBinarizer(
            method=self.config.binarization_method,
            block_size=self.config.adaptive_block_size,
            c=self.config.adaptive_c,
        )
        binarized_img, _ = binarizer.process(enhanced_img, {})

        # Generate lightweight web thumbnail preview
        thumbnail_img = create_thumbnail(enhanced_img, max_edge=self.config.thumbnail_max_edge)

        # Assemble PreprocessingResult
        result = PreprocessingResult(
            enhanced_image=enhanced_img,
            binarized_image=binarized_img,
            thumbnail_image=thumbnail_img,
            applied_skew_angle=float(context.get("applied_skew_angle", 0.0)),
            perspective_corrected=bool(context.get("perspective_corrected", False)),
            contrast_applied=bool(context.get("contrast_applied", True)),
            noise_reduction_applied=bool(context.get("noise_reduction_applied", True)),
            original_width=orig_w,
            original_height=orig_h,
            processed_width=proc_w,
            processed_height=proc_h,
            step_metrics=context.get("step_metrics", {}),
        )

        # Persist derived artifacts to storage/preprocessed
        self.artifact_manager.save_artifacts(certificate_id, result)

        total_time_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "Preprocessed document %s in %.2f ms (orig: %dx%d -> proc: %dx%d, deskew: %.2f°)",
            certificate_id,
            total_time_ms,
            orig_w,
            orig_h,
            proc_w,
            proc_h,
            result.applied_skew_angle,
        )

        return result


_preprocessing_service_instance: Optional[PreprocessingService] = None


def get_preprocessing_service() -> PreprocessingService:
    """Global dependency provider for PreprocessingService."""
    global _preprocessing_service_instance
    if _preprocessing_service_instance is None:
        _preprocessing_service_instance = PreprocessingService()
    return _preprocessing_service_instance
