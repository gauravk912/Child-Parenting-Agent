from datetime import datetime
from typing import List, Optional
from uuid import UUID
from typing_extensions import TypedDict


class CrisisGraphState(TypedDict, total=False):
    child_id: UUID
    parent_message: str

    child_name: Optional[str]
    nickname: Optional[str]
    sensory_triggers: Optional[str]
    calming_strategies: Optional[str]
    school_notes: Optional[str]
    medical_notes: Optional[str]

    route: str
    severity: str
    needs_emergency_support: bool

    classification_source: str
    classification_confidence: float
    classification_reasoning: Optional[str]

    use_graph_memory: bool
    use_tavily_evidence: bool
    use_therapist_notes: bool
    planning_source: str
    planning_confidence: float
    planning_reasoning: Optional[str]

    immediate_actions: List[str]
    response_text: str

    evidence_query: Optional[str]
    evidence_sources: List[dict]
    evidence_summary: Optional[str]

    therapist_note_snippets: List[dict]

    similar_incidents: List[dict]
    prior_helpful_interventions: List[str]
    ranked_interventions: List[dict]
    recurring_contexts: List[str]
    memory_summary: Optional[str]

    retrieval_confidence: float
    ranking_confidence: float
    overall_response_confidence: float
    confidence_note: Optional[str]

    used_child_profile: bool
    used_graph_memory: bool
    used_tavily_evidence: bool
    used_therapist_notes: bool
    used_llm_generation: bool
    safety_guard_applied: bool
    provenance_summary: Optional[str]


class DebriefGraphState(TypedDict, total=False):
    child_id: UUID
    parent_summary: str
    transcript_text: Optional[str]
    raw_text: str

    child_name: Optional[str]
    parent_id: Optional[UUID]

    location: Optional[str]
    outcome_notes: Optional[str]
    interventions_tried: List[str]

    antecedent: Optional[str]
    behavior: Optional[str]
    consequence: Optional[str]

    extraction_source: str
    extraction_confidence: float
    extraction_reasoning: Optional[str]

    trigger_labels: List[str]
    context_labels: List[str]
    behavior_labels: List[str]
    intervention_labels: List[str]
    normalization_source: str
    normalization_confidence: float
    normalization_reasoning: Optional[str]

    debrief_overall_confidence: float
    debrief_confidence_note: Optional[str]

    incident_id: UUID
    created_at: datetime
    graph_updated: bool

    missing_fields: List[str]
    follow_up_question: Optional[str]
    debrief_quality: str


class PredictionGraphState(TypedDict, total=False):
    child_id: UUID
    prediction_date: str
    location_query: Optional[str]

    child_name: Optional[str]
    sensory_triggers: Optional[str]
    calming_strategies: Optional[str]
    school_notes: Optional[str]
    medical_notes: Optional[str]

    weather_summary: Optional[str]
    weather_risk_factors: List[str]

    calendar_summary: Optional[str]
    calendar_risk_factors: List[str]

    risk_score: float
    risk_level: str
    risk_factors: List[str]
    prevention_steps: List[str]

    engineered_features: dict

    prediction_model_source: str
    prediction_model_probability: Optional[float]
    prediction_confidence: float
    prediction_confidence_note: Optional[str]

    prediction_id: UUID
    created_at: datetime


class ReportGraphState(TypedDict, total=False):
    child_id: UUID
    days: int

    child_name: Optional[str]

    incident_count: int
    top_antecedents: List[str]
    top_behaviors: List[str]
    top_consequences: List[str]
    top_interventions: List[str]

    latest_risk_level: Optional[str]
    average_risk_score: Optional[float]

    therapist_note_snippets: List[dict]

    summary_text: str
    next_week_recommendations: List[str]
    confidence_note: Optional[str]

    used_incident_history: bool
    used_prediction_history: bool
    used_therapist_notes: bool
    used_llm_summary: bool
    report_provenance_summary: Optional[str]