"""SQLAlchemy 2.0 ORM models for all 12 relational database tables."""

from app.models.audit_log import AuditLogModel
from app.models.certificate import CertificateModel
from app.models.course_verification import CourseCertificateVerificationModel
from app.models.forensic import ForensicFindingModel
from app.models.issuer_registry import IssuerRegistryModel
from app.models.ml_prediction import MLPredictionModel
from app.models.ocr_field import OCRFieldModel
from app.models.record import InstitutionRecordModel
from app.models.report import VerificationReportModel
from app.models.template import (
    InstitutionModel,
    InstitutionTemplateModel,
    TemplateMatchResultModel,
)
from app.models.text_consistency import TextConsistencyModel
from app.models.user import AppUserModel
from app.models.verification_history import VerificationHistoryModel

__all__ = [
    "InstitutionModel",
    "AppUserModel",
    "CertificateModel",
    "OCRFieldModel",
    "ForensicFindingModel",
    "TextConsistencyModel",
    "TemplateMatchResultModel",
    "MLPredictionModel",
    "VerificationReportModel",
    "InstitutionTemplateModel",
    "InstitutionRecordModel",
    "AuditLogModel",
    "IssuerRegistryModel",
    "CourseCertificateVerificationModel",
    "VerificationHistoryModel",
]
