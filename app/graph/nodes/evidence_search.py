from app.services.tavily_service import search_parenting_evidence


def evidence_search(state):
    severity = state.get("severity", "moderate")
    triggers = state.get("sensory_triggers") or ""
    parent_message = state.get("parent_message", "")

    evidence_query = (
        "trauma informed parenting strategies for child dysregulation "
        f"with sensory overload, severity {severity}, triggers {triggers}, "
        f"incident context: {parent_message}"
    )

    evidence_sources = search_parenting_evidence(evidence_query, max_results=3)

    evidence_summary = " ".join(
        [src.get("snippet", "") for src in evidence_sources]
    )[:1000]

    return {
        **state,
        "evidence_query": evidence_query,
        "evidence_sources": evidence_sources,
        "evidence_summary": evidence_summary,
    }