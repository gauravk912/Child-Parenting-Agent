from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.child import Child
from app.models.incident import Incident
from app.models.prediction import Prediction
from app.models.document import Document
from app.models.intervention import Intervention
from app.services.graph_memory_service import (
    get_similar_incidents_for_child,
    get_recurring_contexts_for_child,
)
from app.services.dedupe_service import normalize_text, dedupe_strings


def _pretty_label(value: str) -> str:
    if not value:
        return value
    value = value.strip()
    if value.lower().startswith("location:"):
        suffix = value.split(":", 1)[1].strip()
        return f"Location: {suffix}"
    return value[:1].upper() + value[1:]


def build_child_analytics(db: Session, child_id: UUID, days: int = 30) -> Dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    child = db.query(Child).filter(Child.id == child_id).first()
    incidents = db.query(Incident).filter(Incident.child_id == child_id, Incident.created_at >= cutoff).all()
    predictions = db.query(Prediction).filter(Prediction.child_id == child_id, Prediction.created_at >= cutoff).all()
    documents = db.query(Document).filter(Document.child_id == child_id).all()
    feedback_rows = db.query(Intervention).filter(Intervention.child_id == child_id).all()

    antecedent_counter = Counter()
    behavior_counter = Counter()
    intervention_counter = Counter()
    risk_level_counter = Counter()
    positive_feedback_counter = Counter()

    risk_points = []

    for incident in incidents:
        if incident.summary:
            antecedent_counter.update([incident.summary[:100]])

    for prediction in predictions:
        if prediction.risk_level:
            risk_level_counter.update([prediction.risk_level])
        if prediction.risk_score is not None:
            risk_points.append(
                {
                    "prediction_date": str(prediction.prediction_date),
                    "risk_score": prediction.risk_score,
                    "risk_level": prediction.risk_level,
                }
            )

    similar_incidents = get_similar_incidents_for_child(child_id=child_id, limit=50)

    for item in similar_incidents:
        behavior = item.get("behavior")
        if behavior:
            behavior_counter.update([behavior[:100]])

        for intervention in item.get("interventions", []) or []:
            if intervention:
                intervention_counter.update([intervention])

    for row in feedback_rows:
        if row.intervention_name:
            intervention_counter.update([row.intervention_name])
            if (row.effectiveness_score or 0.0) >= 0.5:
                positive_feedback_counter.update([row.intervention_name])

    recurring_contexts_raw = get_recurring_contexts_for_child(child_id=child_id, limit=20)
    recurring_contexts_clean = []
    seen_contexts = set()

    for ctx in recurring_contexts_raw:
        key = normalize_text(ctx)
        if not key or key in seen_contexts:
            continue

        if key in {"store outing", "grocery store"}:
            normalized = "Store outing"
        elif key in {"location: grocery store"}:
            normalized = "Location: grocery store"
        else:
            normalized = _pretty_label(ctx)

        pretty_key = normalize_text(normalized)
        if pretty_key in seen_contexts:
            continue

        seen_contexts.add(pretty_key)
        recurring_contexts_clean.append(normalized)

    avg_risk_score = None
    if predictions:
        valid_scores = [p.risk_score for p in predictions if p.risk_score is not None]
        if valid_scores:
            avg_risk_score = round(sum(valid_scores) / len(valid_scores), 2)

    top_antecedents = dedupe_strings([x for x, _ in antecedent_counter.most_common(5)])
    top_behaviors = dedupe_strings([x for x, _ in behavior_counter.most_common(5)])
    top_interventions = dedupe_strings([x for x, _ in intervention_counter.most_common(5)])
    positive_feedback_interventions = dedupe_strings([x for x, _ in positive_feedback_counter.most_common(5)])

    return {
        "child_id": str(child_id),
        "child_name": child.name if child else None,
        "days": days,
        "incident_count": len(incidents),
        "prediction_count": len(predictions),
        "therapist_note_count": len(documents),
        "top_antecedents": top_antecedents,
        "top_behaviors": top_behaviors,
        "top_interventions": top_interventions,
        "positive_feedback_interventions": positive_feedback_interventions,
        "risk_level_distribution": dict(risk_level_counter),
        "average_risk_score": avg_risk_score,
        "risk_trend_points": risk_points[-10:],
        "recurring_contexts": recurring_contexts_clean[:8],
    }