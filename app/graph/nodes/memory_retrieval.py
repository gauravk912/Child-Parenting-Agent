from app.services.graph_memory_service import (
    get_similar_incidents_for_child,
    get_prior_helpful_interventions_for_child,
    get_ranked_interventions_for_child,
    get_recurring_contexts_for_child,
    build_memory_summary,
)


def memory_retrieval(state):
    child_id = state["child_id"]
    parent_message = state.get("parent_message", "")

    similar_incidents = get_similar_incidents_for_child(child_id=child_id, limit=8)
    prior_helpful_interventions = get_prior_helpful_interventions_for_child(child_id=child_id, limit=8)
    ranked_interventions = get_ranked_interventions_for_child(
        child_id=child_id,
        parent_message=parent_message,
        limit=5,
    )
    recurring_contexts = get_recurring_contexts_for_child(child_id=child_id, limit=5)

    memory_summary = build_memory_summary(
        similar_incidents=similar_incidents,
        prior_helpful_interventions=prior_helpful_interventions,
        recurring_contexts=recurring_contexts,
    )

    return {
        **state,
        "similar_incidents": similar_incidents,
        "prior_helpful_interventions": prior_helpful_interventions,
        "ranked_interventions": ranked_interventions,
        "recurring_contexts": recurring_contexts,
        "memory_summary": memory_summary,
    }