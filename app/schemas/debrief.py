from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DebriefRequest(BaseModel):
    child_id: UUID
    parent_summary: str = Field(..., min_length=5, max_length=4000, description="Parent's debrief summary after the incident")
    transcript_text: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None, max_length=200)
    interventions_tried: List[str] = Field(default_factory=list)
    outcome_notes: Optional[str] = Field(default=None, max_length=2000)


class DebriefResponse(BaseModel):
    incident_id: UUID
    child_id: UUID
    child_name: Optional[str] = None

    antecedent: Optional[str] = None
    behavior: Optional[str] = None
    consequence: Optional[str] = None

    extraction_source: Optional[str] = None
    extraction_confidence: Optional[float] = None
    extraction_reasoning: Optional[str] = None

    trigger_labels: List[str] = Field(default_factory=list)
    context_labels: List[str] = Field(default_factory=list)
    behavior_labels: List[str] = Field(default_factory=list)
    intervention_labels: List[str] = Field(default_factory=list)

    normalization_source: Optional[str] = None
    normalization_confidence: Optional[float] = None
    normalization_reasoning: Optional[str] = None

    interventions_tried: List[str] = Field(default_factory=list)
    parent_summary: str
    transcript_text: Optional[str] = None
    outcome_notes: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    graph_updated: bool = False

    debrief_quality: str = "complete"
    missing_fields: List[str] = Field(default_factory=list)
    follow_up_question: Optional[str] = None