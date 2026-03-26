from datetime import datetime, timedelta, timezone
from typing import Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.child import Child
from app.models.incident import Incident
from app.models.prediction import Prediction
from app.services.notification_service import get_notifications_for_child
from app.services.dedupe_service import dedupe_dicts


def build_child_timeline(db: Session, child_id: UUID, days: int = 30) -> Dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    child = db.query(Child).filter(Child.id == child_id).first()
    incidents = db.query(Incident).filter(
        Incident.child_id == child_id,
        Incident.created_at >= cutoff,
    ).all()

    predictions = db.query(Prediction).filter(
        Prediction.child_id == child_id,
        Prediction.created_at >= cutoff,
    ).all()

    notifications = get_notifications_for_child(child_id)

    items: List[Dict] = []

    for incident in incidents:
        items.append(
            {
                "item_type": "incident",
                "item_id": str(incident.id),
                "timestamp": incident.created_at.isoformat() if incident.created_at else "",
                "title": "Incident recorded",
                "summary": incident.summary or "Incident summary unavailable.",
                "metadata": {},
            }
        )

    prediction_items = []
    for prediction in predictions:
        prediction_items.append(
            {
                "item_type": "prediction",
                "item_id": str(prediction.id),
                "timestamp": prediction.created_at.isoformat() if prediction.created_at else "",
                "title": f"Prediction: {prediction.risk_level}",
                "summary": f"Predicted risk score {prediction.risk_score} for {prediction.prediction_date}.",
                "metadata": {
                    "risk_level": prediction.risk_level,
                    "risk_score": prediction.risk_score,
                    "prediction_date": str(prediction.prediction_date),
                },
            }
        )

    prediction_items = dedupe_dicts(
        sorted(prediction_items, key=lambda x: x["timestamp"], reverse=True),
        key_fn=lambda x: (
            x["item_type"],
            x["metadata"].get("prediction_date"),
            x["metadata"].get("risk_level"),
            x["metadata"].get("risk_score"),
        ),
    )

    items.extend(prediction_items)

    notification_items = []
    for notification in notifications:
        created_at = notification.get("created_at", "")
        notification_items.append(
            {
                "item_type": "notification",
                "item_id": notification.get("notification_id", ""),
                "timestamp": created_at,
                "title": notification.get("title", "Notification"),
                "summary": notification.get("message", ""),
                "metadata": {
                    "type": notification.get("type"),
                    "is_read": notification.get("is_read"),
                },
            }
        )

    notification_items = dedupe_dicts(
        sorted(notification_items, key=lambda x: x["timestamp"], reverse=True),
        key_fn=lambda x: (
            x["item_type"],
            x["title"],
            x["summary"],
        ),
    )

    items.extend(notification_items)

    items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "child_id": str(child_id),
        "child_name": child.name if child else None,
        "days": days,
        "item_count": len(items),
        "items": items[:50],
    }