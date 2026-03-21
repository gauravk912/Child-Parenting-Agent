from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ChildBase(BaseModel):
    name: str
    nickname: Optional[str] = None
    birth_date: Optional[date] = None
    age_years: Optional[int] = None
    sensory_triggers: Optional[str] = None
    calming_strategies: Optional[str] = None
    school_notes: Optional[str] = None
    medical_notes: Optional[str] = None


class ChildCreate(ChildBase):
    parent_id: UUID


class ChildUpdate(BaseModel):
    name: Optional[str] = None
    nickname: Optional[str] = None
    birth_date: Optional[date] = None
    age_years: Optional[int] = None
    sensory_triggers: Optional[str] = None
    calming_strategies: Optional[str] = None
    school_notes: Optional[str] = None
    medical_notes: Optional[str] = None


class ChildResponse(ChildBase):
    id: UUID
    parent_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    