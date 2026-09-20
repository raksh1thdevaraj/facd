import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.config import settings
from app.models.template import (
    InstitutionModel,
    InstitutionTemplateModel,
    TemplateMatchResultModel,
)
from app.modules.template_matching.aligner import align_to_template
from app.modules.template_matching.record_verifier import verify_student_record
from app.modules.template_matching.registration_service import (
    load_precomputed_template_features,
)
from app.modules.template_matching.seal_matcher import match_seal_and_logo
from app.modules.template_matching.ssim_evaluator import compute_template_ssim
from app.modules.template_matching.tier_classifier import classify_tier
from app.modules.template_matching.visual_diff import generate_visual_diff
from app.schemas.pipeline import CertificateFields
from app.schemas.template_matching import (
    TemplateMatchMetrics,
    TemplateVerificationResult,
)


class TemplateVerificationService:
    """Orchestrator for visual template matching and student record verification."""

    def __init__(self) -> None:
        settings.ensure_directories_exist()

    def verify(
        self,
        query_img: np.ndarray,
        extracted_fields: CertificateFields,
        db: Session,
        document_id: str,
        certificate_id: Optional[str] = None,
        template_id: Optional[str] = None,
        institution_id: Optional[str] = None,
        forensic_score: float = 1.0,
        text_score: float = 1.0,
        save_to_db: bool = True,
    ) -> TemplateVerificationResult:
        """Execute dual-track template comparison and student record cross-verification.

        Args:
            query_img: Deskewed/preprocessed query certificate image array.
            extracted_fields: Extracted OCR fields.
            db: Database session.
            document_id: Tracking document UUID.
            certificate_id: Optional database certificate UUID.
            template_id: Optional explicit template UUID.
            institution_id: Optional explicit institution UUID.
            forensic_score: Authenticity score from forensic engine [0.0, 1.0].
            text_score: Consistency score from text consistency engine [0.0, 1.0].
            save_to_db: Whether to persist findings to template_match_results table.

        Returns:
            TemplateVerificationResult.
        """
        t0 = time.perf_counter()

        # 1. Resolve Institution
        target_inst: Optional[InstitutionModel] = None
        if institution_id:
            target_inst = (
                db.query(InstitutionModel).filter(InstitutionModel.id == institution_id).first()
            )
        elif extracted_fields.institution_name:
            # Fuzzy match institution name
            all_insts = db.query(InstitutionModel).all()
            best_ratio = 0.0
            for inst in all_insts:
                ratio = fuzz.token_sort_ratio(
                    extracted_fields.institution_name.lower(), inst.name.lower()
                )
                if ratio > best_ratio and ratio >= 70.0:
                    best_ratio = ratio
                    target_inst = inst

        resolved_inst_id = target_inst.id if target_inst else institution_id
        resolved_inst_name = target_inst.name if target_inst else extracted_fields.institution_name

        # 2. Resolve Master Template
        template_model: Optional[InstitutionTemplateModel] = None
        if template_id:
            template_model = (
                db.query(InstitutionTemplateModel)
                .filter(InstitutionTemplateModel.id == template_id)
                .first()
            )
        elif resolved_inst_id:
            query_tpl = db.query(InstitutionTemplateModel).filter(
                InstitutionTemplateModel.institution_id == resolved_inst_id
            )
            # Try to match degree program if available
            if extracted_fields.course_degree:
                for tpl in query_tpl.all():
                    if (
                        tpl.degree_program
                        and fuzz.token_sort_ratio(
                            extracted_fields.course_degree.lower(), tpl.degree_program.lower()
                        )
                        >= 75.0
                    ):
                        template_model = tpl
                        break
            if not template_model:
                template_model = query_tpl.first()

        # 3. Visual Template Comparison (if master template exists)
        template_metrics: Optional[TemplateMatchMetrics] = None
        visual_diff_path: Optional[str] = None

        if template_model and Path(template_model.image_path).exists():
            tpl_img = cv2.imread(template_model.image_path)
            if tpl_img is not None:
                # Load precomputed features if available
                precomputed = None
                if template_model.feature_data_path:
                    precomputed = load_precomputed_template_features(
                        template_model.feature_data_path
                    )

                # Feature alignment & warping
                aligned_img, inlier_ratio, align_ok = align_to_template(
                    query_img=query_img,
                    template_img=tpl_img,
                    precomputed_template_descriptors=precomputed,
                )

                # Generate variable text mask if defined
                var_mask = None
                if template_model.variable_regions_json:
                    var_mask = np.zeros(tpl_img.shape[:2], dtype=np.uint8)
                    for reg in template_model.variable_regions_json:
                        rx = int(reg.get("x", 0))
                        ry = int(reg.get("y", 0))
                        rw = int(reg.get("width", reg.get("w", 0)))
                        rh = int(reg.get("height", reg.get("h", 0)))
                        var_mask[ry : ry + rh, rx : rx + rw] = 1

                # Structural Similarity (SSIM)
                ssim_score, diff_map = compute_template_ssim(
                    aligned_img=aligned_img,
                    template_img=tpl_img,
                    variable_mask=var_mask,
                )

                # Seal / Logo correlation
                seal_score = 0.85
                if template_model.seal_roi_json:
                    seal_score, _, _ = match_seal_and_logo(
                        aligned_img=aligned_img,
                        template_img=tpl_img,
                        seal_roi=template_model.seal_roi_json,
                    )

                # Composite visual score
                if align_ok:
                    overall_visual = float(
                        0.50 * ssim_score + 0.25 * inlier_ratio + 0.25 * seal_score
                    )
                else:
                    overall_visual = float(0.40 * ssim_score + 0.10 * seal_score)

                template_metrics = TemplateMatchMetrics(
                    ssim_score=round(ssim_score, 4),
                    feature_similarity_score=round(inlier_ratio, 4),
                    seal_match_score=round(seal_score, 4),
                    overall_template_score=round(np.clip(overall_visual, 0.0, 1.0), 4),
                    alignment_success=align_ok,
                    inlier_ratio=round(inlier_ratio, 4),
                )

                # Generate visual diff panel
                diff_file = settings.REPORT_DIR / f"{document_id}_template_diff.png"
                generate_visual_diff(aligned_img, tpl_img, diff_map, output_path=str(diff_file))
                visual_diff_path = str(diff_file)

        # 4. Database Student Record Cross-Verification
        record_res = verify_student_record(
            extracted_fields=extracted_fields,
            db=db,
            institution_id=resolved_inst_id,
        )

        # 5. Three-Tier Decision Classification
        tier_class = classify_tier(
            record_result=record_res,
            template_metrics=template_metrics,
            forensic_score=forensic_score,
            text_score=text_score,
        )

        execution_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        # 6. Database Persistence
        if save_to_db and certificate_id:
            try:
                db_result = TemplateMatchResultModel(
                    certificate_id=certificate_id,
                    template_id=template_model.id if template_model else None,
                    institution_id=resolved_inst_id,
                    ssim_score=template_metrics.ssim_score if template_metrics else 0.0,
                    feature_score=template_metrics.feature_similarity_score
                    if template_metrics
                    else 0.0,
                    seal_score=template_metrics.seal_match_score if template_metrics else 0.0,
                    overall_score=template_metrics.overall_template_score
                    if template_metrics
                    else 0.0,
                    tier_status=tier_class.tier.value,
                    record_found=record_res.record_found,
                    discrepancies_json=tier_class.discrepancies,
                    visual_diff_path=visual_diff_path,
                )
                db.add(db_result)
                db.commit()
            except Exception:
                db.rollback()

        return TemplateVerificationResult(
            document_id=document_id,
            template_id=template_model.id if template_model else None,
            template_name=template_model.template_name if template_model else None,
            institution_id=resolved_inst_id,
            institution_name=resolved_inst_name,
            template_metrics=template_metrics,
            record_result=record_res,
            tier_classification=tier_class,
            visual_diff_path=visual_diff_path,
            execution_time_ms=execution_ms,
        )
