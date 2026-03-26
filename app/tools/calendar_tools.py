from typing import Dict, Optional

from app.core.config import settings
from app.mcp.client import is_server_enabled
from app.mcp.adapters.google_calendar_adapter import fetch_calendar_context


def get_calendar_tool_context(prediction_date: Optional[str] = None) -> Dict:
    if settings.enable_mcp_calendar_adapter and is_server_enabled("calendar"):
        return fetch_calendar_context(prediction_date=prediction_date)

    return {
        "calendar_summary": "Calendar tool unavailable.",
        "calendar_risk_factors": ["Calendar tool unavailable; transitions should still be considered conservatively."],
    }