import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from app.core.config import settings

logger = logging.getLogger(__name__)


def _calendar_file_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    return project_root / settings.local_calendar_data_file


def _load_calendar_data():
    path = _calendar_file_path()
    if not path.exists():
        logger.warning("Calendar data file not found at %s", path)
        return {}

    raw = json.loads(path.read_text(encoding="utf-8"))

    # Case 1: already dict keyed by date
    if isinstance(raw, dict):
        return raw

    # Case 2: list of event dicts -> convert to dict keyed by YYYY-MM-DD
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

    logger.warning("Calendar data file had unsupported format.")
    return {}


def get_calendar_context(prediction_date: str) -> Dict[str, Any]:
    """
    Always returns:
    {
        "summary": str,
        "risk_factors": list[str]
    }
    """
    if not settings.enable_mcp_calendar_adapter:
        logger.info("Calendar adapter disabled. Using fallback calendar context.")
        return {
            "summary": f"No calendar context available for {prediction_date}.",
            "risk_factors": [
                "No calendar context available; normal daily transitions should still be considered."
            ],
        }

    logger.info("Loading local calendar context for date=%s", prediction_date)

    data = _load_calendar_data()
    events = data.get(prediction_date, [])

    if not events:
        return {
            "summary": f"No calendar events found for {prediction_date}.",
            "risk_factors": [
                "No major scheduled events detected; normal daily transitions should still be considered."
            ],
        }

    normalized_events: List[Dict[str, Any]] = []
    for event in events:
        if isinstance(event, str):
            normalized_events.append({"title": event, "start_time": None})
        elif isinstance(event, dict):
            normalized_events.append(
                {
                    "title": event.get("title", "Untitled event"),
                    "start_time": event.get("start_time") or event.get("start"),
                }
            )

    summary_parts = []
    risk_factors = []

    for event in normalized_events:
        title = str(event.get("title", "Untitled event"))
        start_time = event.get("start_time")

        if start_time:
            summary_parts.append(f"{title} at {start_time}")
        else:
            summary_parts.append(title)

        lowered = title.lower()

        if any(x in lowered for x in ["drop-off", "school", "therapy", "appointment", "pickup"]):
            risk_factors.append(f"Scheduled event may increase transition load: {title}")

        if any(x in lowered for x in ["errand", "store", "shopping", "visit", "grandparents"]):
            risk_factors.append(f"Potential overstimulating outing or schedule disruption: {title}")

        if any(x in lowered for x in ["routine", "wind-down", "bedtime"]):
            risk_factors.append(f"Routine anchor available later in the day: {title}")

    if len(normalized_events) >= 3:
        risk_factors.append("Multiple planned events may increase transition fatigue today.")

    summary = "Upcoming calendar events: " + "; ".join(summary_parts)

    if not risk_factors:
        risk_factors.append(
            "Calendar loaded successfully, but no major transition-heavy events were detected."
        )

    return {
        "summary": summary,
        "risk_factors": risk_factors,
    }