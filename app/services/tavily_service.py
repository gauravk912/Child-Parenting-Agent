import logging
from typing import List, Dict

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def search_support_evidence(query: str, max_results: int = 3) -> List[Dict]:
    """
    Returns a list like:
    [
      {
        "title": "...",
        "url": "...",
        "snippet": "..."
      }
    ]
    """
    if not settings.enable_live_evidence_search:
        logger.info("Tavily search disabled by config.")
        return []

    if not settings.tavily_api_key:
        logger.warning("TAVILY_API_KEY missing. Returning no evidence.")
        return []

    try:
        logger.info("Calling Tavily search for query=%s", query)

        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=20,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", []) or []

        cleaned = []
        for item in results[:max_results]:
            cleaned.append(
                {
                    "title": item.get("title", "Untitled"),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", "")[:500],
                }
            )

        return cleaned

    except Exception as e:
        logger.exception("Tavily search failed: %s", str(e))
        return []