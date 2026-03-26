from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field


FeedbackLabel = Literal["helpful", "partial", "not_helpful"]


class InterventionFeedbackRequest(BaseModel):
    child_id: UUID
    intervention_name: str = Field(..., min_length=2, max_length=200)
    effectiveness_label: FeedbackLabel
    context_note: Optional[str] = Field(default=None, max_length=1000)
    feedback_note: Optional[str] = Field(default=None, max_length=2000)


class InterventionFeedbackResponse(BaseModel):
    feedback_id: UUID
    child_id: UUID
    intervention_name: str
    effectiveness_label: str
    effectiveness_score: float
    context_note: Optional[str] = None
    feedback_note: Optional[str] = None
    created_at: Optional[datetime] = None