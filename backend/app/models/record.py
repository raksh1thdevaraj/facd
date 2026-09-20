import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.database import Base


class InstitutionRecordModel(Base):
    """SQLAlchemy model for authentic graduation records issued by institutions."""

    __tablename__ = "institution_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    institution_id = Column(String(36), nullable=False, index=True)
    student_name = Column(String(255), nullable=False, index=True)
    roll_number = Column(String(128), nullable=False, index=True)
    degree_name = Column(String(255), nullable=False)
    passing_year = Column(Integer, nullable=False, index=True)
    cgpa = Column(Float, nullable=True)
    issue_date = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
