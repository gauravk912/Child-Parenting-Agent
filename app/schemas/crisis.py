from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CrisisEvidenceSource(BaseModel):
    title: str
    url: str
    snippet: str


class CrisisProvenance(BaseModel):
    used_child_profile: bool = False
    used_graph_memory: bool = False
    used_tavily_evidence: bool = False
    used_llm_generation: bool = False
    safety_guard_applied: bool = False
    provenance_summary: Optional[str] = None


class CrisisRequest(BaseModel):
    child_id: UUID
    parent_message: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Live message from parent during a tantrum or crisis"
    )


class CrisisResponse(BaseModel):
    child_id: UUID
    child_name: Optional[str] = None
    route: str
    severity: str
    needs_emergency_support: bool
    immediate_actions: List[str]
    response_text: str
    evidence_sources: List[CrisisEvidenceSource] = Field(default_factory=list)
    memory_summary: Optional[str] = None
    prior_helpful_interventions: List[str] = Field(default_factory=list)
    provenance: CrisisProvenance