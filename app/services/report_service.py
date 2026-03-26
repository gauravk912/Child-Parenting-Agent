from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models.child import Child
from app.models.incident import Incident
from app.models.prediction import Prediction


def _top_values(values: List[str], limit: int = 3) -> List[str]:
    cleaned = [v.strip() for v in values if v and v.strip()]
    return [item for item, _ in Counter(cleaned).most_common(limit)]


def get_weekly_child_data(child_id: UUID, days: int = 7) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        child = db.query(Child).filter(Child.id == child_id).first()
        if not child:
            raise ValueError("Child not found for weekly report.")

        incidents = (
            db.query(Incident)
            .options(
                joinedload(Incident.abc_record),
                joinedload(Incident.interventions),
            )
            .filter(Incident.child_id == child_id, Incident.created_at >= cutoff)
            .order_by(Incident.created_at.desc())
            .all()
        )

        predictions = (
            db.query(Prediction)
            .filter(Prediction.child_id == child_id, Prediction.created_at >= cutoff)
            .order_by(Prediction.created_at.desc())
            .all()
        )

        antecedents = []
        behaviors = []
        consequences = []
        interventions = []

        for incident in incidents:
            if incident.abc_record:
                antecedents.append(incident.abc_record.antecedent or "")
                behaviors.append(incident.abc_record.behavior or "")
                consequences.append(incident.abc_record.consequence or "")
            for intervention in incident.interventions:
                interventions.append(intervention.name or "")

        avg_risk = None
        latest_risk = None
        if predictions:
            latest_risk = predictions[0].risk_level
            avg_risk = round(sum(p.risk_score for p in predictions) / len(predictions), 2)

        return {
            "child_id": child_id,
            "child_name": child.name,
            "days": days,
            "incident_count": len(incidents),
            "top_antecedents": _top_values(antecedents),
            "top_behaviors": _top_values(behaviors),
            "top_consequences": _top_values(consequences),
            "top_interventions": _top_values(interventions),
            "latest_risk_level": latest_risk,
            "average_risk_score": avg_risk,
            "incidents": incidents,
            "predictions": predictions,
        }
    finally:
        db.close()