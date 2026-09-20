from app.modules.template_matching.aligner import align_to_template
from app.modules.template_matching.diagnostics import run_template_diagnostics
from app.modules.template_matching.record_importer import import_records_from_csv
from app.modules.template_matching.record_verifier import verify_student_record
from app.modules.template_matching.registration_service import (
    load_precomputed_template_features,
    register_institution_template,
)
from app.modules.template_matching.seal_matcher import match_seal_and_logo
from app.modules.template_matching.service import TemplateVerificationService
from app.modules.template_matching.ssim_evaluator import (
    compute_template_ssim,
    evaluate_ssim_category,
)
from app.modules.template_matching.tier_classifier import classify_tier
from app.modules.template_matching.visual_diff import generate_visual_diff

__all__ = [
    "align_to_template",
    "compute_template_ssim",
    "evaluate_ssim_category",
    "match_seal_and_logo",
    "verify_student_record",
    "classify_tier",
    "register_institution_template",
    "load_precomputed_template_features",
    "import_records_from_csv",
    "generate_visual_diff",
    "run_template_diagnostics",
    "TemplateVerificationService",
]
