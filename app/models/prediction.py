import uuid

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id"), nullable=False, index=True)

    prediction_date = Column(Date, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)

    weather_summary = Column(Text, nullable=True)
    calendar_summary = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    child = relationship("Child", back_populates="predictions")