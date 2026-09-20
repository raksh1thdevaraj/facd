from typing import Any, Optional, Union

import numpy as np

from app.schemas.forensics import ForensicAnalysisResult
from app.schemas.ingestion import IngestedDocument
from app.schemas.ml_prediction import FeatureVector
from app.schemas.pipeline import (
    CertificateFields,
    ForensicsOutput,
    IngestionOutput,
    OCROutput,
    TemplateMatchOutput,
    TextConsistencyOutput,
)
from app.schemas.template_matching import (
    RecordVerificationResult,
    TemplateVerificationResult,
)
from app.schemas.text_consistency import TextConsistencyResult


class TabularFeatureExtractor:
    """Extracts a standardized 22-dimensional float32 feature vector from upstream stages."""

    STANDARD_A4_ASPECT_RATIO = 1.4142

    def extract_from_upstream(
        self,
        ingestion_data: Any = None,
        ocr_result: Any = None,
        text_consistency_result: Any = None,
        forensics_result: Any = None,
        template_result: Any = None,
        record_result: Any = None,
    ) -> FeatureVector:
        """Alias mapping upstream pipeline outputs to extract()."""
        return self.extract(
            ingestion=ingestion_data,
            ocr=ocr_result,
            text_consistency=text_consistency_result,
            forensics=forensics_result,
            template_match=template_result,
            record_result=record_result,
        )

    def extract(
        self,
        ingestion: Optional[Union[IngestedDocument, IngestionOutput, dict]] = None,
        ocr: Optional[Union[OCROutput, dict]] = None,
        fields: Optional[Union[CertificateFields, dict]] = None,
        text_consistency: Optional[
            Union[TextConsistencyResult, TextConsistencyOutput, dict]
        ] = None,
        forensics: Optional[Union[ForensicAnalysisResult, ForensicsOutput, dict]] = None,
        template_match: Optional[
            Union[TemplateVerificationResult, TemplateMatchOutput, dict]
        ] = None,
        record_result: Optional[Union[RecordVerificationResult, dict]] = None,
    ) -> FeatureVector:
        """Construct the 22-dimensional tabular feature vector with robust fallback imputation.

        Args:
            ingestion: Ingestion output or document metadata.
            ocr: OCR engine output.
            fields: Structured certificate fields.
            text_consistency: Typographical & logical consistency analysis result.
            forensics: Digital image forensics result (ELA, clones, noise).
            template_match: Template visual matching and verification result.
            record_result: Student record cross-verification result.

        Returns:
            Validated FeatureVector instance.
        """
        # ----------------------------------------------------------------------
        # Group A: Ingestion & Metadata (4 features)
        # ----------------------------------------------------------------------
        file_size_kb = 500.0
        has_exif = 0.0
        software_editing_flag = 0.0
        aspect_ratio_deviation = 0.0

        if ingestion is not None:
            if isinstance(ingestion, dict):
                if "file_size_kb" in ingestion:
                    file_size_kb = float(ingestion["file_size_kb"])
                else:
                    file_size_kb = float(ingestion.get("file_size_bytes", 512000)) / 1024.0

                meta = ingestion.get("metadata", {})
                if isinstance(meta, dict):
                    has_exif = 1.0 if (meta.get("has_exif") or ingestion.get("has_exif")) else 0.0
                    software_editing_flag = (
                        1.0
                        if (
                            meta.get("software")
                            or meta.get("software_editing_detected")
                            or ingestion.get("software_editing_flag")
                            or ingestion.get("software_editing_detected")
                        )
                        else 0.0
                    )
                else:
                    has_exif = 1.0 if ingestion.get("has_exif") else 0.0
                    software_editing_flag = (
                        1.0
                        if (
                            ingestion.get("software_editing_detected")
                            or ingestion.get("software_editing_flag")
                        )
                        else 0.0
                    )

                if "aspect_ratio_deviation" in ingestion:
                    aspect_ratio_deviation = float(ingestion["aspect_ratio_deviation"])
                elif (
                    isinstance(ingestion.get("quality_metrics"), dict)
                    and "aspect_ratio_deviation" in ingestion["quality_metrics"]
                ):
                    aspect_ratio_deviation = float(
                        ingestion["quality_metrics"]["aspect_ratio_deviation"]
                    )
                else:
                    w = float(ingestion.get("image_width", 1000) or 1000)
                    h = float(ingestion.get("image_height", 1414) or 1414)
                    if h > 0 and w > 0:
                        ratio = max(w / h, h / w)
                        aspect_ratio_deviation = abs(ratio - self.STANDARD_A4_ASPECT_RATIO)
            elif isinstance(ingestion, IngestedDocument):
                file_size_kb = float(ingestion.metadata.file_size_bytes) / 1024.0
                has_exif = 1.0 if ingestion.metadata.exif_data else 0.0
                software_editing_flag = 1.0 if ingestion.metadata.software_editing_detected else 0.0
                w = float(ingestion.metadata.image_width or 1000)
                h = float(ingestion.metadata.image_height or 1414)
                if h > 0 and w > 0:
                    ratio = max(w / h, h / w)
                    aspect_ratio_deviation = abs(ratio - self.STANDARD_A4_ASPECT_RATIO)
            elif isinstance(ingestion, IngestionOutput):
                file_size_kb = float(ingestion.file_size_bytes) / 1024.0
                aspect_ratio_deviation = 0.0

        # ----------------------------------------------------------------------
        # Group B: OCR & Text Quality (4 features)
        # ----------------------------------------------------------------------
        ocr_mean_confidence = 0.85
        ocr_min_confidence = 0.80
        flagged_field_count = 0.0
        missing_critical_fields_count = 0.0

        extracted_fields_obj: Optional[CertificateFields] = None
        if isinstance(fields, CertificateFields):
            extracted_fields_obj = fields
        elif isinstance(fields, dict):
            extracted_fields_obj = CertificateFields(**fields)
        elif isinstance(ocr, OCROutput):
            extracted_fields_obj = ocr.fields

        if isinstance(ocr, OCROutput):
            ocr_mean_confidence = float(ocr.average_ocr_confidence)
            if ocr.tokens:
                token_confs = [t.confidence for t in ocr.tokens]
                ocr_min_confidence = float(min(token_confs)) if token_confs else 0.80
        elif isinstance(ocr, dict):
            ocr_mean_confidence = float(
                ocr.get(
                    "ocr_mean_confidence",
                    ocr.get("mean_confidence", ocr.get("average_ocr_confidence", 0.85)),
                )
            )
            ocr_min_confidence = float(
                ocr.get("ocr_min_confidence", ocr.get("min_confidence", 0.80))
            )
            if "flagged_field_count" in ocr:
                flagged_field_count = float(ocr["flagged_field_count"])
            elif "flagged_fields" in ocr and isinstance(ocr["flagged_fields"], list):
                flagged_field_count = float(len(ocr["flagged_fields"]))
            if "missing_critical_fields_count" in ocr:
                missing_critical_fields_count = float(ocr["missing_critical_fields_count"])
            elif "missing_critical_fields" in ocr and isinstance(
                ocr["missing_critical_fields"], list
            ):
                missing_critical_fields_count = float(len(ocr["missing_critical_fields"]))

        if extracted_fields_obj:
            field_confs = [
                extracted_fields_obj.student_name_confidence,
                extracted_fields_obj.register_number_confidence,
                extracted_fields_obj.institution_name_confidence,
                extracted_fields_obj.course_degree_confidence,
                extracted_fields_obj.grade_or_marks_confidence,
                extracted_fields_obj.issue_date_confidence,
            ]
            valid_confs = [c for c in field_confs if c > 0.0]
            if valid_confs:
                ocr_min_confidence = min(ocr_min_confidence, min(valid_confs))
            flagged_field_count = float(sum(1 for c in valid_confs if c < 0.70))

            critical_checks = [
                extracted_fields_obj.student_name,
                extracted_fields_obj.register_number,
                extracted_fields_obj.institution_name,
                extracted_fields_obj.course_degree,
                extracted_fields_obj.issue_date,
            ]
            missing_critical_fields_count = float(sum(1 for v in critical_checks if not v))

        # ----------------------------------------------------------------------
        # Group C: Text Consistency (5 features)
        # ----------------------------------------------------------------------
        baseline_score = 1.0
        font_size_score = 1.0
        stroke_weight_score = 1.0
        spacing_score = 1.0
        logical_score = 1.0

        if isinstance(text_consistency, TextConsistencyResult):
            baseline_score = float(text_consistency.baseline_score)
            font_size_score = float(text_consistency.font_size_score)
            stroke_weight_score = float(text_consistency.stroke_weight_score)
            spacing_score = float(text_consistency.spacing_score)
            logical_score = float(text_consistency.logical_score)
        elif isinstance(text_consistency, TextConsistencyOutput):
            risk = text_consistency.consistency_risk_score
            cleanliness = max(0.0, min(1.0, 1.0 - (risk / 100.0)))
            baseline_score = cleanliness
            font_size_score = cleanliness
            stroke_weight_score = cleanliness
            spacing_score = cleanliness
            logical_score = cleanliness
        elif isinstance(text_consistency, dict):
            src = text_consistency.get("metrics", text_consistency)
            baseline_score = float(
                src.get("baseline_alignment_score", src.get("baseline_score", 1.0))
            )
            font_size_score = float(
                src.get("font_size_consistency_score", src.get("font_size_score", 1.0))
            )
            stroke_weight_score = float(src.get("stroke_weight_score", 1.0))
            spacing_score = float(src.get("character_spacing_score", src.get("spacing_score", 1.0)))
            logical_score = float(
                src.get("logical_consistency_score", src.get("logical_score", 1.0))
            )

        # ----------------------------------------------------------------------
        # Group D: Image Forensics (4 features)
        # ----------------------------------------------------------------------
        ela_score = 0.90
        copy_move_score = 1.0
        cloned_regions_count = 0.0
        noise_inconsistency_score = 0.90

        if isinstance(forensics, ForensicAnalysisResult):
            ela_score = float(forensics.ela_score)
            copy_move_score = float(forensics.copy_move_score)
            cloned_regions_count = float(len(forensics.detected_clones))
            noise_inconsistency_score = float(forensics.noise_inconsistency_score)
        elif isinstance(forensics, ForensicsOutput):
            ela_score = float(1.0 - forensics.ela_score)
            copy_move_score = float(1.0 - forensics.copy_move_score)
            cloned_regions_count = float(forensics.copy_move_clusters_count)
            noise_inconsistency_score = float(1.0 - forensics.noise_inconsistency_score)
        elif isinstance(forensics, dict):
            ela_score = float(forensics.get("ela_score", 0.90))
            copy_move_score = float(forensics.get("copy_move_score", 1.0))
            cloned_regions_count = float(forensics.get("cloned_regions_count", 0.0))
            noise_inconsistency_score = float(forensics.get("noise_inconsistency_score", 0.90))

        # ----------------------------------------------------------------------
        # Group E: Template & Record Matching (5 features)
        # ----------------------------------------------------------------------
        template_ssim_score = 0.85
        template_feature_score = 0.80
        seal_match_score = 0.85
        record_found_flag = 0.0
        record_match_score = 0.50

        if isinstance(template_match, TemplateVerificationResult):
            if template_match.template_metrics:
                template_ssim_score = float(template_match.template_metrics.ssim_score)
                template_feature_score = float(
                    template_match.template_metrics.feature_similarity_score
                )
                seal_match_score = float(template_match.template_metrics.seal_match_score)
            record_found_flag = 1.0 if template_match.record_result.record_found else 0.0
            record_match_score = float(template_match.record_result.name_match_score)
        elif isinstance(template_match, TemplateMatchOutput):
            if template_match.layout_similarity_score is not None:
                template_ssim_score = float(template_match.layout_similarity_score)
            if template_match.logo_signature_similarity is not None:
                seal_match_score = float(template_match.logo_signature_similarity)
            record_found_flag = 1.0 if template_match.record_found else 0.0
            matches = template_match.record_field_matches
            if matches:
                record_match_score = float(sum(1.0 for v in matches.values() if v) / len(matches))
        elif isinstance(template_match, dict):
            template_ssim_score = float(
                template_match.get("template_ssim_score", template_match.get("ssim_score", 0.85))
            )
            template_feature_score = float(
                template_match.get(
                    "template_feature_score",
                    template_match.get("feature_match_score", 0.80),
                )
            )
            seal_match_score = float(template_match.get("seal_match_score", 0.85))
            record_found_flag = (
                1.0
                if (template_match.get("record_found") or template_match.get("record_found_flag"))
                else 0.0
            )
            record_match_score = float(template_match.get("record_match_score", 0.50))

        if isinstance(record_result, RecordVerificationResult):
            record_found_flag = 1.0 if record_result.record_found else 0.0
            record_match_score = float(record_result.name_match_score)
        elif isinstance(record_result, dict):
            record_found_flag = 1.0 if record_result.get("record_found") else 0.0
            record_match_score = float(record_result.get("name_match_score", 0.50))

        # ----------------------------------------------------------------------
        # Assembly and Numerical Sanitization
        # ----------------------------------------------------------------------
        def _sanitize(val: float, min_v: float = 0.0, max_v: float = 1.0) -> float:
            if np.isnan(val) or np.isinf(val):
                return (min_v + max_v) / 2.0
            return float(np.clip(val, min_v, max_v))

        return FeatureVector(
            file_size_kb=float(max(0.0, file_size_kb)),
            has_exif=_sanitize(has_exif, 0.0, 1.0),
            software_editing_flag=_sanitize(software_editing_flag, 0.0, 1.0),
            aspect_ratio_deviation=float(max(0.0, aspect_ratio_deviation)),
            ocr_mean_confidence=_sanitize(ocr_mean_confidence, 0.0, 1.0),
            ocr_min_confidence=_sanitize(ocr_min_confidence, 0.0, 1.0),
            flagged_field_count=float(max(0.0, flagged_field_count)),
            missing_critical_fields_count=float(max(0.0, missing_critical_fields_count)),
            baseline_alignment_score=_sanitize(baseline_score, 0.0, 1.0),
            font_size_consistency_score=_sanitize(font_size_score, 0.0, 1.0),
            stroke_weight_score=_sanitize(stroke_weight_score, 0.0, 1.0),
            character_spacing_score=_sanitize(spacing_score, 0.0, 1.0),
            logical_consistency_score=_sanitize(logical_score, 0.0, 1.0),
            ela_score=_sanitize(ela_score, 0.0, 1.0),
            copy_move_score=_sanitize(copy_move_score, 0.0, 1.0),
            cloned_regions_count=float(max(0.0, cloned_regions_count)),
            noise_inconsistency_score=_sanitize(noise_inconsistency_score, 0.0, 1.0),
            template_ssim_score=_sanitize(template_ssim_score, 0.0, 1.0),
            template_feature_score=_sanitize(template_feature_score, 0.0, 1.0),
            seal_match_score=_sanitize(seal_match_score, 0.0, 1.0),
            record_found_flag=_sanitize(record_found_flag, 0.0, 1.0),
            record_match_score=_sanitize(record_match_score, 0.0, 1.0),
        )

    def extract_vector(self, **kwargs: Any) -> np.ndarray:
        """Convenience method returning directly the 22D float32 NumPy array."""
        feat_obj = self.extract(**kwargs)
        return feat_obj.to_numpy()
