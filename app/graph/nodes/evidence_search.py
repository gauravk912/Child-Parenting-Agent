from app.services.tavily_service import search_support_evidence


def evidence_search(state):
    if not state.get("use_tavily_evidence", False):
        return {
            **state,
            "evidence_query": None,
            "evidence_sources": [],
            "evidence_summary": "External evidence skipped by planner.",
        }

    parent_message = state.get("parent_message", "")
    sensory_triggers = state.get("sensory_triggers") or ""
    severity = state.get("severity", "moderate")

    query = f"{parent_message} trauma-informed child regulation strategies {sensory_triggers} severity {severity}"

    evidence_sources = search_support_evidence(query=query, max_results=3)

    return {
        **state,
        "evidence_query": query,
        "evidence_sources": evidence_sources,
        "evidence_summary": f"Retrieved {len(evidence_sources)} external evidence sources.",
    }