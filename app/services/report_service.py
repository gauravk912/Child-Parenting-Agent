from collections import Counter
from typing import Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.child import Child
from app.models.incident import Incident
from app.models.prediction import Prediction
from app.models.abc_record import ABCRecord
from app.models.intervention import Intervention
from app.retrieval.retriever import retrieve_therapist_note_snippets
from app.services.llm_service import generate_weekly_report_summary
from app.services.graph_memory_service import get_similar_incidents_for_child
from app.services.dedupe_service import dedupe_strings, dedupe_dicts, normalize_text


def _build_parent_prompt(child_name: str, report_data: Dict) -> str:
    return f"""
Write a warm, clear weekly parent summary for {child_name}.

Data:
- incident_count: {report_data["incident_count"]}
- top_antecedents: {report_data["top_antecedents"]}
- top_behaviors: {report_data["top_behaviors"]}
- top_consequences: {report_data["top_consequences"]}
- top_interventions: {report_data["top_interventions"]}
- latest_risk_level: {report_data["latest_risk_level"]}
- average_risk_score: {report_data["average_risk_score"]}
- therapist_note_snippets: {report_data["therapist_note_snippets"]}
- positive_feedback_interventions: {report_data["positive_feedback_interventions"]}

Keep the tone supportive and practical.
Do not sound clinical.
"""


def _build_therapist_prompt(child_name: str, report_data: Dict) -> str:
    return f"""
Write a structured therapist-facing weekly summary for {child_name}.

Data:
- incident_count: {report_data["incident_count"]}
- top_antecedents: {report_data["top_antecedents"]}
- top_behaviors: {report_data["top_behaviors"]}
- top_consequences: {report_data["top_consequences"]}
- top_interventions: {report_data["top_interventions"]}
- latest_risk_level: {report_data["latest_risk_level"]}
- average_risk_score: {report_data["average_risk_score"]}
- therapist_note_snippets: {report_data["therapist_note_snippets"]}
- positive_feedback_interventions: {report_data["positive_feedback_interventions"]}

Use more structured and observation-oriented wording.
Avoid diagnosis.
"""


def build_weekly_report_data(
    db: Session,
    child_id: UUID,
    days: int,
) -> Dict:
    child = db.query(Child).filter(Child.id == child_id).first()
    incidents = db.query(Incident).filter(Incident.child_id == child_id).all()
    predictions = db.query(Prediction).filter(Prediction.child_id == child_id).all()
    abc_rows = (
        db.query(ABCRecord)
        .join(Incident, ABCRecord.incident_id == Incident.id)
        .filter(Incident.child_id == child_id)
        .all()
    )
    feedback_rows = db.query(Intervention).filter(Intervention.child_id == child_id).all()

    antecedent_counter = Counter()
    behavior_counter = Counter()
    consequence_counter = Counter()
    intervention_counter = Counter()
    positive_feedback_counter = Counter()

    for incident in incidents:
        if incident.summary:
            antecedent_counter.update([incident.summary[:100]])

    for abc in abc_rows:
        if abc.antecedent:
            antecedent_counter.update([abc.antecedent[:100]])
        if abc.behavior:
            behavior_counter.update([abc.behavior[:100]])
        if abc.consequence:
            consequence_counter.update([abc.consequence[:100]])

    graph_incidents = get_similar_incidents_for_child(child_id=child_id, limit=30)
    for item in graph_incidents:
        behavior = item.get("behavior")
        if behavior:
            behavior_counter.update([behavior[:100]])

        consequence = item.get("consequence")
        if consequence:
            consequence_counter.update([consequence[:100]])

        for intervention in item.get("interventions", []) or []:
            if intervention:
                intervention_counter.update([intervention])

    for row in feedback_rows:
        if row.intervention_name:
            intervention_counter.update([row.intervention_name])
            if (row.effectiveness_score or 0.0) >= 0.5:
                positive_feedback_counter.update([row.intervention_name])

    latest_risk_level = predictions[-1].risk_level if predictions else None
    avg_risk_score = None
    if predictions:
        scores = [p.risk_score for p in predictions if p.risk_score is not None]
        if scores:
            avg_risk_score = round(sum(scores) / len(scores), 2)

    snippets = retrieve_therapist_note_snippets(
        child_id=child_id,
        query_text="weekly summary triggers interventions regulation patterns",
        top_k=5,
    )
    snippets = dedupe_dicts(
        snippets,
        key_fn=lambda x: (
            str(x.get("document_id", "")),
            normalize_text(x.get("title")),
            normalize_text(x.get("chunk_text")),
        ),
        max_items=3,
    )

    top_antecedents = dedupe_strings([x for x, _ in antecedent_counter.most_common(6)], max_items=5)
    top_behaviors = dedupe_strings([x for x, _ in behavior_counter.most_common(6)], max_items=5)
    top_consequences = dedupe_strings([x for x, _ in consequence_counter.most_common(6)], max_items=5)
    top_interventions = dedupe_strings([x for x, _ in intervention_counter.most_common(6)], max_items=5)
    positive_feedback_interventions = dedupe_strings([x for x, _ in positive_feedback_counter.most_common(5)], max_items=5)

    return {
        "child_name": child.name if child else None,
        "incident_count": len(incidents),
        "top_antecedents": top_antecedents,
        "top_behaviors": top_behaviors,
        "top_consequences": top_consequences,
        "top_interventions": top_interventions,
        "positive_feedback_interventions": positive_feedback_interventions,
        "latest_risk_level": latest_risk_level,
        "average_risk_score": avg_risk_score,
        "therapist_note_snippets": snippets,
    }


def generate_weekly_report(
    db: Session,
    child_id: UUID,
    days: int,
    view_type: str,
) -> Dict:
    report_data = build_weekly_report_data(db=db, child_id=child_id, days=days)
    child_name = report_data.get("child_name") or "the child"

    if view_type == "therapist":
        prompt = _build_therapist_prompt(child_name, report_data)
        structured_flags = {
            "tone": "clinical-light",
            "audience": "therapist",
        }
    else:
        prompt = _build_parent_prompt(child_name, report_data)
        structured_flags = {
            "tone": "supportive",
            "audience": "parent",
        }

    summary_text = generate_weekly_report_summary(prompt)

    return {
        **report_data,
        "summary_text": summary_text,
        "next_week_recommendations": [
            "Continue using the most successful calming supports proactively.",
            "Prepare for the most common trigger situations before they happen.",
            "Keep routines and transitions predictable where possible.",
            "Plan shorter outings and include a low-stimulation exit option.",
            "Use calming tools before known trigger periods rather than after escalation.",
        ],
        "confidence_note": "Higher confidence because incident history, ABC details, graph memory, feedback data, prediction history, and therapist note context were available.",
        "structured_flags": structured_flags,
    }