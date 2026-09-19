import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, String

from app.database import Base


class TextConsistencyModel(Base):
    """SQLAlchemy model for storing text consistency and typographical forensics results."""

    __tablename__ = "text_consistency_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id = Column(String(36), index=True, nullable=False)
    overall_score = Column(Float, nullable=False)
    baseline_score = Column(Float, nullable=False)
    font_size_score = Column(Float, nullable=False)
    stroke_weight_score = Column(Float, nullable=False)
    spacing_score = Column(Float, nullable=False)
    format_score = Column(Float, nullable=False, default=1.0)
    logical_score = Column(Float, nullable=False)
    anomalous_regions_json = Column(JSON, nullable=True, default=list)
    visualization_image_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
