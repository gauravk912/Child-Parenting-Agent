from app.services.llm_service import plan_crisis_tool_usage


def _fallback_plan(state):
    message = (state.get("parent_message") or "").lower()
    severity = state.get("severity", "moderate")

    use_graph_memory = True
    use_therapist_notes = True

    use_tavily_evidence = False
    if severity in {"high", "emergency"}:
        use_tavily_evidence = True
    if any(x in message for x in ["public", "store", "school", "unsafe", "violent", "hurting", "throwing"]):
        use_tavily_evidence = True

    return {
        **state,
        "use_graph_memory": use_graph_memory,
        "use_tavily_evidence": use_tavily_evidence,
        "use_therapist_notes": use_therapist_notes,
        "planning_source": "rule_fallback",
        "planning_confidence": 0.70,
        "planning_reasoning": "Rule-based planner selected tools from severity and message context.",
    }


def tool_planner(state):
    try:
        result = plan_crisis_tool_usage(
            child_name=state.get("child_name"),
            severity=state.get("severity"),
            parent_message=state.get("parent_message", ""),
            sensory_triggers=state.get("sensory_triggers"),
            school_notes=state.get("school_notes"),
        )

        return {
            **state,
            "use_graph_memory": result.get("use_graph_memory", True),
            "use_tavily_evidence": result.get("use_tavily_evidence", False),
            "use_therapist_notes": result.get("use_therapist_notes", True),
            "planning_source": "llm",
            "planning_confidence": result.get("confidence", 0.0),
            "planning_reasoning": result.get("reasoning_summary"),
        }
    except Exception:
        return _fallback_plan(state)