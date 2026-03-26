import uuid

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)

    hashed_password = Column(String, nullable=True)
    auth_provider = Column(String, nullable=False, default="local")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)