from typing import Dict, List, Tuple

from app.modules.ocr.field_extractors.base_extractor import ExtractedField
from app.schemas.ocr import ExtractedFieldDTO
from app.schemas.pipeline import CertificateFields, OCRToken


class ConfidenceEvaluator:
    """Evaluates field-level confidence scores, applies manual-review thresholds (<0.70),
    and maps to schemas.
    """

    def __init__(self, threshold: float = 0.70):
        self.threshold = threshold

    def evaluate_and_map_fields(
        self,
        extracted_fields: Dict[str, ExtractedField],
        all_tokens: List[OCRToken],
    ) -> Tuple[CertificateFields, Dict[str, ExtractedFieldDTO], bool, float]:
        """Evaluate fields, compute average confidence, flag low confidence,
        and build CertificateFields.
        """
        field_dtos: Dict[str, ExtractedFieldDTO] = {}
        has_low_confidence = False

        cert_fields = CertificateFields()

        for name, field in extracted_fields.items():
            is_flagged = field.confidence < self.threshold
            if is_flagged:
                has_low_confidence = True
            field.is_flagged = is_flagged

            field_dto = ExtractedFieldDTO(
                field_name=field.field_name,
                value=field.value,
                raw_text=field.raw_text,
                confidence=round(field.confidence, 4),
                is_flagged=is_flagged,
                bbox=field.bounding_box,
                pixel_bbox=field.pixel_bounding_box,
            )
            field_dtos[name] = field_dto

            # Map into canonical CertificateFields
            if name == "student_name":
                cert_fields.student_name = field.value
                cert_fields.student_name_confidence = field.confidence
            elif name == "register_number":
                cert_fields.register_number = field.value
                cert_fields.register_number_confidence = field.confidence
            elif name == "institution_name":
                cert_fields.institution_name = field.value
                cert_fields.institution_name_confidence = field.confidence
            elif name == "course_degree":
                cert_fields.course_degree = field.value
                cert_fields.course_degree_confidence = field.confidence
            elif name == "grade_or_marks":
                cert_fields.grade_or_marks = field.value
                cert_fields.grade_or_marks_confidence = field.confidence
            elif name == "issue_date":
                cert_fields.issue_date = field.value
                cert_fields.issue_date_confidence = field.confidence
            elif name == "certificate_number":
                cert_fields.certificate_number = field.value
                cert_fields.certificate_number_confidence = field.confidence

        # Compute average confidence
        if all_tokens:
            avg_conf = sum(t.confidence for t in all_tokens) / len(all_tokens)
        elif extracted_fields:
            avg_conf = sum(f.confidence for f in extracted_fields.values()) / len(extracted_fields)
        else:
            avg_conf = 0.0

        return cert_fields, field_dtos, has_low_confidence, round(avg_conf, 4)
