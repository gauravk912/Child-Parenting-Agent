from typing import Dict, Optional

from app.core.config import settings
from app.mcp.client import is_server_enabled
from app.mcp.adapters.weather_adapter import fetch_weather_context


def get_weather_tool_context(location_query: Optional[str] = None) -> Dict:
    if settings.enable_mcp_weather_adapter and is_server_enabled("weather"):
        return fetch_weather_context(location_query=location_query)

    return {
        "weather_summary": "Weather tool unavailable.",
        "weather_risk_factors": ["Weather tool unavailable; environmental conditions should still be considered conservatively."],
    }