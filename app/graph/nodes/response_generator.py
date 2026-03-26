from app.services.llm_service import generate_crisis_response, load_prompt_template
from app.tools.vector_tools import get_therapist_note_tool_context


def response_generator(state):
    child_name = state.get("child_name") or "your child"
    severity = state.get("severity", "moderate")
    parent_message = state.get("parent_message", "")
    triggers = state.get("sensory_triggers") or "not specified"
    calming = state.get("calming_strategies") or "not specified"
    immediate_actions = state.get("immediate_actions", [])
    evidence_sources = state.get("evidence_sources", [])
    similar_incidents = state.get("similar_incidents", [])
    prior_helpful_interventions = state.get("prior_helpful_interventions", [])
    ranked_interventions = state.get("ranked_interventions", [])
    recurring_contexts = state.get("recurring_contexts", [])
    memory_summary = state.get("memory_summary", "No prior incident memory available.")

    therapist_note_snippets = get_therapist_note_tool_context(
        child_id=state["child_id"],
        query_text=parent_message,
        top_k=3,
    )

    if severity == "emergency":
        response_text = (
            f"This may be an emergency involving {child_name}. "
            f"Please focus on immediate physical safety first. "
            f"If there is trouble breathing, major injury, loss of consciousness, "
            f"or danger to self or others, contact emergency services right away."
        )
        return {
            **state,
            "response_text": response_text,
            "therapist_note_snippets": therapist_note_snippets,
            "used_child_profile": True,
            "used_graph_memory": bool(prior_helpful_interventions or recurring_contexts or (memory_summary and memory_summary != 'No prior incident memory available.')),
            "used_tavily_evidence": bool(evidence_sources),
            "used_therapist_notes": bool(therapist_note_snippets),
            "used_llm_generation": False,
            "provenance_summary": "Used child profile, deterministic emergency response, and safety-first logic.",
        }

    evidence_block = "\n".join(
        [
            f"- Title: {src['title']}\n  URL: {src['url']}\n  Snippet: {src['snippet']}"
            for src in evidence_sources
        ]
    )

    actions_block = "\n".join([f"- {item}" for item in immediate_actions])

    incidents_block = "\n".join(
        [
            f"- Antecedent: {item.get('antecedent')}; Behavior: {item.get('behavior')}; Consequence: {item.get('consequence')}; Interventions: {item.get('interventions')}"
            for item in similar_incidents
        ]
    )

    therapist_block = "\n".join(
        [
            f"- Title: {item.get('title')}; Snippet: {item.get('chunk_text')}"
            for item in therapist_note_snippets
        ]
    )

    ranked_block = "\n".join(
        [
            f"- Rank {item.get('rank')}: {item.get('intervention')} (used {item.get('use_count')} times)"
            for item in ranked_interventions
        ]
    )

    recurring_block = ", ".join(recurring_contexts) if recurring_contexts else "None known"
    prior_helpful_block = ", ".join(prior_helpful_interventions) if prior_helpful_interventions else "None known"

    prompt_template = load_prompt_template("crisis.txt")

    prompt = f"""
{prompt_template}

CHILD CONTEXT
Child name: {child_name}
Known sensory triggers: {triggers}
Known calming strategies: {calming}

CURRENT INCIDENT
Severity: {severity}
Parent message: {parent_message}

IMMEDIATE ACTIONS ALREADY PLANNED
{actions_block}

PRIOR MEMORY SUMMARY
{memory_summary}

SIMILAR INCIDENTS
{incidents_block if incidents_block else "No similar incidents available."}

RECURRING CONTEXTS
{recurring_block}

PREVIOUSLY USED INTERVENTIONS
{prior_helpful_block}

RANKED INTERVENTIONS
{ranked_block if ranked_block else "No ranked interventions available."}

THERAPIST NOTE SNIPPETS
{therapist_block if therapist_block else "No therapist note snippets available."}

EVIDENCE SOURCES
{evidence_block if evidence_block else "No external evidence available."}
"""

    llm_text = generate_crisis_response(prompt)

    provenance_parts = ["child profile"]
    if prior_helpful_interventions or recurring_contexts or (memory_summary and memory_summary != "No prior incident memory available."):
        provenance_parts.append("graph memory")
    if therapist_note_snippets:
        provenance_parts.append("therapist notes")
    if evidence_sources:
        provenance_parts.append("Tavily evidence")
    provenance_parts.append("LLM generation")

    return {
        **state,
        "response_text": llm_text,
        "therapist_note_snippets": therapist_note_snippets,
        "used_child_profile": True,
        "used_graph_memory": bool(prior_helpful_interventions or recurring_contexts or (memory_summary and memory_summary != "No prior incident memory available.")),
        "used_tavily_evidence": bool(evidence_sources),
        "used_therapist_notes": bool(therapist_note_snippets),
        "used_llm_generation": True,
        "provenance_summary": "Used " + ", ".join(provenance_parts) + ".",
    }