import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id"), nullable=False, index=True)

    intervention_name = Column(String, nullable=False, index=True)
    context_note = Column(Text, nullable=True)

    effectiveness_label = Column(String, nullable=True)
    effectiveness_score = Column(Float, nullable=True)
    feedback_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    child = relationship("Child")