import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from uuid import UUID, uuid4

from app.core.config import settings


def _notification_store_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    path = project_root / settings.local_notification_store_file
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_notifications() -> List[Dict]:
    path = _notification_store_path()
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_notifications(items: List[Dict]) -> None:
    path = _notification_store_path()
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def build_high_risk_notification(
    child_id: UUID,
    child_name: str,
    prediction_date: str,
    risk_score: float,
    prevention_steps: List[str],
) -> Dict:
    top_step = prevention_steps[0] if prevention_steps else "Review calming supports before high-risk periods."

    return {
        "notification_id": str(uuid4()),
        "child_id": str(child_id),
        "type": "high_risk_prediction",
        "title": f"High-risk day predicted for {child_name}",
        "message": (
            f"{child_name} has a high predicted stress/risk level ({risk_score}) for {prediction_date}. "
            f"Suggested first step: {top_step}"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_read": False,
    }


def save_notification(notification: Dict) -> None:
    items = _load_notifications()
    items.append(notification)
    _save_notifications(items)


def get_notifications_for_child(child_id: UUID) -> List[Dict]:
    items = _load_notifications()
    child_str = str(child_id)
    return [item for item in items if item.get("child_id") == child_str]