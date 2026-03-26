from app.services.graph_memory_service import (
    get_similar_incidents_for_child,
    get_prior_helpful_interventions_for_child,
    get_ranked_interventions_for_child,
    get_recurring_contexts_for_child,
    build_memory_summary,
)
from app.tools.vector_tools import get_therapist_note_tool_context
from app.services.dedupe_service import dedupe_dicts


def memory_retrieval(state):
    if not state.get("use_graph_memory", True):
        return {
            **state,
            "similar_incidents": [],
            "prior_helpful_interventions": [],
            "ranked_interventions": [],
            "recurring_contexts": [],
            "memory_summary": "Graph memory skipped by planner.",
            "therapist_note_snippets": [],
            "retrieval_confidence": 0.45 if state.get("use_therapist_notes", False) else 0.25,
            "ranking_confidence": 0.0,
        }

    child_id = state["child_id"]
    parent_message = state.get("parent_message", "")

    similar_incidents = get_similar_incidents_for_child(child_id=child_id, limit=12)
    prior_helpful_interventions = get_prior_helpful_interventions_for_child(child_id=child_id, limit=8)
    ranked_interventions = get_ranked_interventions_for_child(
        child_id=child_id,
        parent_message=parent_message,
        limit=5,
    )
    recurring_contexts = get_recurring_contexts_for_child(child_id=child_id, limit=6)

    memory_summary = build_memory_summary(
        similar_incidents=similar_incidents,
        prior_helpful_interventions=prior_helpful_interventions,
        recurring_contexts=recurring_contexts,
    )

    therapist_note_snippets = []
    if state.get("use_therapist_notes", True):
        therapist_note_snippets = get_therapist_note_tool_context(
            child_id=child_id,
            query_text=parent_message,
            top_k=5,
        )
        therapist_note_snippets = dedupe_dicts(
            therapist_note_snippets,
            key_fn=lambda x: (
                str(x.get("document_id", "")),
                str(x.get("title", "")).strip().lower(),
                str(x.get("chunk_text", "")).strip().lower(),
            ),
            max_items=3,
        )

    retrieval_confidence = 0.30
    if similar_incidents:
        retrieval_confidence += 0.25
    if recurring_contexts:
        retrieval_confidence += 0.15
    if therapist_note_snippets:
        retrieval_confidence += 0.20
    retrieval_confidence = min(round(retrieval_confidence, 2), 0.95)

    ranking_confidence = 0.20
    if ranked_interventions:
        ranking_confidence += 0.20
        if len(ranked_interventions) >= 3:
            ranking_confidence += 0.15
        if ranked_interventions[0].get("contextual_score", 0) >= 10:
            ranking_confidence += 0.15
        if ranked_interventions[0].get("feedback_adjustment", 0) > 0:
            ranking_confidence += 0.10
    ranking_confidence = min(round(ranking_confidence, 2), 0.95)

    return {
        **state,
        "similar_incidents": similar_incidents,
        "prior_helpful_interventions": prior_helpful_interventions,
        "ranked_interventions": ranked_interventions,
        "recurring_contexts": recurring_contexts,
        "memory_summary": memory_summary,
        "therapist_note_snippets": therapist_note_snippets,
        "retrieval_confidence": retrieval_confidence,
        "ranking_confidence": ranking_confidence,
    }