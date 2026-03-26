from app.services.graph_memory_service import (
    get_similar_incidents_for_child,
    get_prior_helpful_interventions_for_child,
    build_memory_summary,
)


def memory_retrieval(state):
    child_id = state["child_id"]

    similar_incidents = get_similar_incidents_for_child(child_id=child_id, limit=5)
    prior_helpful_interventions = get_prior_helpful_interventions_for_child(child_id=child_id, limit=5)

    memory_summary = build_memory_summary(
        similar_incidents=similar_incidents,
        prior_helpful_interventions=prior_helpful_interventions,
    )

    return {
        **state,
        "similar_incidents": similar_incidents,
        "prior_helpful_interventions": prior_helpful_interventions,
        "memory_summary": memory_summary,
    }