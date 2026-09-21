import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text

from app.database import Base


class InstitutionModel(Base):
    """SQLAlchemy model for registered academic institutions."""

    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(64), nullable=True, index=True)
    domain = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class InstitutionTemplateModel(Base):
    """SQLAlchemy model for registered certificate master templates."""

    __tablename__ = "institution_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), nullable=False, index=True)
    template_name = Column(String(255), nullable=False)
    degree_program = Column(String(255), nullable=True)
    effective_year_start = Column(Integer, nullable=True)
    effective_year_end = Column(Integer, nullable=True)
    image_path = Column(String(512), nullable=False)
    feature_data_path = Column(String(512), nullable=True)
    seal_roi_json = Column(JSON, nullable=True, default=dict)
    variable_regions_json = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class TemplateMatchResultModel(Base):
    """SQLAlchemy model for storing template and record comparison results."""

    __tablename__ = "template_match_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id = Column(String(36), index=True, nullable=False)
    template_id = Column(String(36), nullable=True, index=True)
    institution_id = Column(String(36), nullable=True, index=True)
    ssim_score = Column(Float, nullable=False, default=0.0)
    feature_score = Column(Float, nullable=False, default=0.0)
    seal_score = Column(Float, nullable=False, default=0.0)
    overall_score = Column(Float, nullable=False, default=0.0)
    tier_status = Column(String(64), nullable=False)
    record_found = Column(Boolean, nullable=False, default=False)
    discrepancies_json = Column(JSON, nullable=True, default=list)
    discrepancy_notes = Column(Text, nullable=True)
    visual_diff_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
