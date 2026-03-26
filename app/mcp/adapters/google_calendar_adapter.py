from typing import Dict, Optional
import logging

from app.services.calendar_service import get_calendar_context

logger = logging.getLogger(__name__)


def fetch_calendar_context(prediction_date: Optional[str] = None) -> Dict:
    logger.info("Calendar MCP adapter called for prediction_date=%s", prediction_date)
    return get_calendar_context(prediction_date=prediction_date)