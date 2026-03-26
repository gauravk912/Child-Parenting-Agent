import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Child(Base):
    __tablename__ = "children"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    name = Column(String, nullable=False)
    nickname = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    age_years = Column(Integer, nullable=True)

    sensory_triggers = Column(Text, nullable=True)
    calming_strategies = Column(Text, nullable=True)
    school_notes = Column(Text, nullable=True)
    medical_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    parent = relationship("User")
    incidents = relationship("Incident", back_populates="child", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="child", cascade="all, delete-orphan")
    interventions = relationship("Intervention", cascade="all, delete-orphan")