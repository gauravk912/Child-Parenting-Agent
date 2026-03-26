from typing import List, Dict
import logging

from tavily import TavilyClient

from app.core.config import settings

logger = logging.getLogger(__name__)


def search_parenting_evidence(query: str, max_results: int = 3) -> List[Dict]:
    if not settings.enable_live_evidence_search:
        logger.info("Tavily evidence search skipped because enable_live_evidence_search is false")
        return []

    if not settings.tavily_api_key:
        logger.info("Tavily evidence search skipped because TAVILY_API_KEY is missing")
        return []

    logger.info("Running Tavily evidence search")

    client = TavilyClient(api_key=settings.tavily_api_key)

    response = client.search(
        query=query,
        max_results=max_results,
        search_depth="basic",
        include_answer=False,
    )

    results = response.get("results", [])

    cleaned = []
    for item in results:
        cleaned.append(
            {
                "title": item.get("title", "Untitled Source"),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:400],
            }
        )

    logger.info("Tavily evidence search returned %s results", len(cleaned))
    return cleaned