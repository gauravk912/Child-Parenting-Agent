from typing import Dict, Optional
import logging

from app.core.config import settings
from app.services.weather_service import get_weather_context

logger = logging.getLogger(__name__)


def fetch_weather_context(location_query: Optional[str] = None) -> Dict:
    logger.info("Weather MCP adapter called for location=%s", location_query or settings.default_weather_location)
    return get_weather_context(location_query=location_query)