from app.services.llm_service import normalize_incident_memory


def _fallback_labels(state):
    parent_summary = (state.get("parent_summary") or "").lower()
    antecedent = (state.get("antecedent") or "").lower()
    behavior = (state.get("behavior") or "").lower()
    location = (state.get("location") or "").lower()
    interventions = [x.lower() for x in state.get("interventions_tried", []) if isinstance(x, str)]

    trigger_labels = []
    context_labels = []
    behavior_labels = []
    intervention_labels = []

    combined_context = " ".join([parent_summary, antecedent, location])

    if "after school" in combined_context:
        trigger_labels.append("after school transition")
    if "crowded" in combined_context:
        context_labels.append("crowded environment")
    if "store" in combined_context or "grocery" in combined_context:
        context_labels.append("store outing")
    if "loud" in combined_context or "noise" in combined_context:
        context_labels.append("loud environment")
    if "transition" in combined_context:
        trigger_labels.append("transition demand")

    combined_behavior = " ".join([parent_summary, behavior])
    if "scream" in combined_behavior or "yell" in combined_behavior:
        behavior_labels.append("screaming")
    if "throw" in combined_behavior:
        behavior_labels.append("throwing objects")
    if "drop" in combined_behavior or "floor" in combined_behavior:
        behavior_labels.append("dropping to floor")

    for item in interventions:
        if "deep pressure" in item:
            intervention_labels.append("deep pressure")
        elif "quiet corner" in item:
            intervention_labels.append("quiet corner")
        elif "favorite toy" in item or "toy" in item:
            intervention_labels.append("favorite toy")
        else:
            intervention_labels.append(item)

    return {
        "trigger_labels": list(dict.fromkeys(trigger_labels)),
        "context_labels": list(dict.fromkeys(context_labels)),
        "behavior_labels": list(dict.fromkeys(behavior_labels)),
        "intervention_labels": list(dict.fromkeys(intervention_labels)),
        "normalization_source": "rule_fallback",
        "normalization_confidence": 0.55,
        "normalization_reasoning": "Rule-based normalization fallback used.",
    }


def memory_normalizer(state):
    try:
        normalized = normalize_incident_memory(
            parent_summary=state.get("parent_summary", ""),
            antecedent=state.get("antecedent"),
            behavior=state.get("behavior"),
            consequence=state.get("consequence"),
            location=state.get("location"),
            interventions_tried=state.get("interventions_tried", []),
        )
        return {
            **state,
            "trigger_labels": normalized.get("trigger_labels", []),
            "context_labels": normalized.get("context_labels", []),
            "behavior_labels": normalized.get("behavior_labels", []),
            "intervention_labels": normalized.get("intervention_labels", []),
            "normalization_source": "llm",
            "normalization_confidence": normalized.get("confidence", 0.0),
            "normalization_reasoning": normalized.get("reasoning_summary"),
        }
    except Exception:
        fallback = _fallback_labels(state)
        return {
            **state,
            **fallback,
        }