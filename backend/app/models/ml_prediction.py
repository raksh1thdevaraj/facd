"""SQLAlchemy ORM model for ML manipulation predictions."""

import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, String

from app.database import Base


class MLPredictionModel(Base):
    """SQLAlchemy model for persisting machine learning manipulation predictions."""

    __tablename__ = "ml_predictions"
    __table_args__ = {"extend_existing": True}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id = Column(String(36), index=True, nullable=False)
    model_version = Column(String(64), nullable=False)
    model_type = Column(String(64), nullable=False, default="tabular_baseline")
    manipulation_probability = Column(Float, nullable=False)
    predicted_class = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    feature_vector_json = Column(JSON, nullable=True)
    feature_contributions_json = Column(JSON, nullable=True)
    execution_time_ms = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
