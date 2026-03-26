import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _load_calendar_events() -> List[dict]:
    project_root = Path(__file__).resolve().parents[2]
    file_path = project_root / settings.local_calendar_data_file

    if not file_path.exists():
        raise FileNotFoundError(f"Calendar data file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Calendar data file must contain a list of events.")

    return data


def get_calendar_context(prediction_date: Optional[str] = None) -> Dict:
    try:
        events = _load_calendar_events()

        target_date = (
            datetime.fromisoformat(prediction_date).date()
            if prediction_date
            else date.today()
        )

        logger.info("Loading local calendar context for date=%s", target_date.isoformat())

        day_events = []
        for event in events:
            start_raw = event.get("start")
            if not start_raw:
                continue

            try:
                start_dt = datetime.fromisoformat(start_raw)
            except Exception:
                continue

            if start_dt.date() == target_date:
                day_events.append(event)

        if not day_events:
            return {
                "calendar_summary": f"No calendar events found for {target_date.isoformat()}.",
                "calendar_risk_factors": [
                    "No major scheduled events detected; normal daily transitions should still be considered."
                ],
            }

        day_events.sort(key=lambda x: x.get("start", ""))

        summaries: List[str] = []
        risk_factors: List[str] = []

        for event in day_events:
            title = event.get("title", "Untitled event")
            start = event.get("start", "unspecified time")
            category = (event.get("category") or "").lower()

            summaries.append(f"{title} at {start}")

            lowered = f"{title} {category}".lower()

            if any(word in lowered for word in ["school", "therapy", "appointment", "doctor", "dentist"]):
                risk_factors.append(f"Scheduled event may increase transition load: {title}")

            if any(word in lowered for word in ["travel", "visit", "party", "errand", "shopping"]):
                risk_factors.append(f"Potential overstimulating outing or schedule disruption: {title}")

            if "routine" in lowered:
                risk_factors.append(f"Routine anchor available later in the day: {title}")

        if len(day_events) >= 3:
            risk_factors.append("Multiple planned events may increase transition fatigue today.")

        if not risk_factors:
            risk_factors.append("No major high-risk calendar events detected, but scheduled transitions should still be monitored.")

        summary = "Upcoming calendar events: " + "; ".join(summaries)

        return {
            "calendar_summary": summary,
            "calendar_risk_factors": risk_factors,
        }

    except Exception:
        logger.exception("Local calendar lookup failed")
        return {
            "calendar_summary": "Local calendar unavailable. Using fallback calendar context.",
            "calendar_risk_factors": [
                "Calendar lookup failed, so schedule-related transitions should still be considered conservatively."
            ],
        }