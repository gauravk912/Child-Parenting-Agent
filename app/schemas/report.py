from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WeeklyReportRequest(BaseModel):
    child_id: UUID
    days: int = Field(default=7, ge=1, le=30)


class WeeklyReportTherapistSnippet(BaseModel):
    document_id: str
    title: str
    chunk_text: str
    score: float


class ReportProvenance(BaseModel):
    used_incident_history: bool = False
    used_prediction_history: bool = False
    used_therapist_notes: bool = False
    used_llm_summary: bool = False
    provenance_summary: Optional[str] = None


class WeeklyReportResponse(BaseModel):
    child_id: UUID
    child_name: Optional[str] = None
    days: int

    incident_count: int
    top_antecedents: List[str] = Field(default_factory=list)
    top_behaviors: List[str] = Field(default_factory=list)
    top_consequences: List[str] = Field(default_factory=list)
    top_interventions: List[str] = Field(default_factory=list)

    latest_risk_level: Optional[str] = None
    average_risk_score: Optional[float] = None

    therapist_note_snippets: List[WeeklyReportTherapistSnippet] = Field(default_factory=list)

    summary_text: str
    next_week_recommendations: List[str] = Field(default_factory=list)

    confidence_note: Optional[str] = None
    provenance: ReportProvenance