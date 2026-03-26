from typing import List, Optional, Dict
from uuid import UUID

from pydantic import BaseModel, Field


class AnalyticsRiskPoint(BaseModel):
    prediction_date: str
    risk_score: float
    risk_level: str


class ChildAnalyticsResponse(BaseModel):
    child_id: UUID
    child_name: Optional[str] = None
    days: int

    incident_count: int
    prediction_count: int
    therapist_note_count: int

    top_antecedents: List[str] = Field(default_factory=list)
    top_behaviors: List[str] = Field(default_factory=list)
    top_interventions: List[str] = Field(default_factory=list)
    positive_feedback_interventions: List[str] = Field(default_factory=list)

    risk_level_distribution: Dict[str, int] = Field(default_factory=dict)
    average_risk_score: Optional[float] = None

    risk_trend_points: List[AnalyticsRiskPoint] = Field(default_factory=list)
    recurring_contexts: List[str] = Field(default_factory=list)