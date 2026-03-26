import json
import os
import sys
from datetime import timedelta
from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression
from sqlalchemy.orm import Session

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.child import Child
from app.models.incident import Incident


def load_calendar_data():
    calendar_path = Path(PROJECT_ROOT) / settings.local_calendar_data_file
    if not calendar_path.exists():
        return {}

    raw = json.loads(calendar_path.read_text(encoding="utf-8"))

    # Case 1: already date-keyed dict
    if isinstance(raw, dict):
        return raw

    # Case 2: list of events -> convert to date-keyed dict
    if isinstance(raw, list):
        converted = {}
        for item in raw:
            if not isinstance(item, dict):
                continue

            event_date = (
                item.get("date")
                or item.get("event_date")
                or item.get("prediction_date")
            )

            if not event_date:
                start = item.get("start_time") or item.get("start")
                if isinstance(start, str) and len(start) >= 10:
                    event_date = start[:10]

            if not event_date:
                continue

            converted.setdefault(event_date, []).append(item)

        return converted

    return {}


def build_calendar_features(calendar_data, target_date_str):
    events = calendar_data.get(target_date_str, [])
    titles = []

    for e in events:
        if isinstance(e, dict):
            titles.append((e.get("title") or "").lower())
        elif isinstance(e, str):
            titles.append(e.lower())

    calendar_risk_count = 0
    is_transition_heavy_day = False
    has_appointment_day = False
    has_outing_risk = False
    has_routine_anchor = False

    for title in titles:
        if any(x in title for x in ["drop-off", "therapy", "appointment", "errand", "visit"]):
            calendar_risk_count += 1
        if any(x in title for x in ["drop-off", "therapy", "appointment"]):
            has_appointment_day = True
        if any(x in title for x in ["errand", "visit", "store", "shopping", "grandparents"]):
            has_outing_risk = True
        if any(x in title for x in ["routine", "wind-down", "bedtime"]):
            has_routine_anchor = True

    if len(events) >= 3:
        is_transition_heavy_day = True
        calendar_risk_count += 1

    if has_routine_anchor:
        calendar_risk_count += 1

    return {
        "calendar_risk_count": float(calendar_risk_count),
        "is_transition_heavy_day": float(is_transition_heavy_day),
        "has_appointment_day": float(has_appointment_day),
        "has_outing_risk": float(has_outing_risk),
        "has_routine_anchor": float(has_routine_anchor),
    }


def main():
    db: Session = SessionLocal()

    try:
        calendar_data = load_calendar_data()

        children = db.query(Child).all()
        if not children:
            print("No children found. Cannot train prediction model.")
            return

        X = []
        y = []

        feature_names = [
            "has_sensory_trigger_profile",
            "has_calming_strategies",
            "has_school_risk_context",
            "has_medical_context",
            "recent_incident_count_7d",
            "recent_incident_count_3d",
            "calendar_risk_count",
            "is_transition_heavy_day",
            "has_appointment_day",
            "has_outing_risk",
            "has_routine_anchor",
        ]

        for child in children:
            incidents = db.query(Incident).filter(Incident.child_id == child.id).all()
            incident_dates = [i.created_at.date() for i in incidents if i.created_at]

            if not incident_dates:
                continue

            min_date = min(incident_dates) - timedelta(days=14)
            max_date = max(incident_dates) + timedelta(days=14)

            current = min_date
            while current <= max_date:
                label = 1 if current in incident_dates else 0

                prior_7 = sum(1 for d in incident_dates if current - timedelta(days=7) <= d < current)
                prior_3 = sum(1 for d in incident_dates if current - timedelta(days=3) <= d < current)

                calendar_feats = build_calendar_features(calendar_data, str(current))

                row = {
                    "has_sensory_trigger_profile": float(bool(child.sensory_triggers)),
                    "has_calming_strategies": float(bool(child.calming_strategies)),
                    "has_school_risk_context": float(bool(child.school_notes)),
                    "has_medical_context": float(bool(child.medical_notes)),
                    "recent_incident_count_7d": float(prior_7),
                    "recent_incident_count_3d": float(prior_3),
                    **calendar_feats,
                }

                X.append([row[name] for name in feature_names])
                y.append(label)

                current += timedelta(days=1)

        if len(X) < 20 or len(set(y)) < 2:
            print("Not enough training variety/data to train model yet.")
            return

        model = LogisticRegression(max_iter=1000)
        model.fit(X, y)

        model_path = Path(PROJECT_ROOT) / settings.local_prediction_model_file
        feature_path = Path(PROJECT_ROOT) / settings.local_prediction_feature_file
        model_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(model, model_path)
        feature_path.write_text(json.dumps(feature_names, indent=2), encoding="utf-8")

        print(f"Saved model to {model_path}")
        print(f"Saved feature list to {feature_path}")

    finally:
        db.close()


if __name__ == "__main__":
    main()