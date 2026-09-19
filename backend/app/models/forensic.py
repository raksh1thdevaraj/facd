import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, String, Text

from app.database import Base


class ForensicFindingModel(Base):
    """SQLAlchemy model for storing digital image forensic findings and suspicious regions."""

    __tablename__ = "forensic_findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id = Column(String(36), index=True, nullable=False)
    finding_type = Column(String(64), nullable=False)
    confidence_score = Column(Float, nullable=False)
    bounding_box_json = Column(JSON, nullable=True, default=dict)
    description = Column(Text, nullable=True)
    heatmap_image_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
