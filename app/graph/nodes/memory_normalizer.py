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
        norm_source = "llm"
        norm_conf = normalized.get("confidence", 0.0)
        norm_reason = normalized.get("reasoning_summary")
        labels = {
            "trigger_labels": normalized.get("trigger_labels", []),
            "context_labels": normalized.get("context_labels", []),
            "behavior_labels": normalized.get("behavior_labels", []),
            "intervention_labels": normalized.get("intervention_labels", []),
        }
    except Exception:
        fallback = _fallback_labels(state)
        norm_source = fallback["normalization_source"]
        norm_conf = fallback["normalization_confidence"]
        norm_reason = fallback["normalization_reasoning"]
        labels = {
            "trigger_labels": fallback["trigger_labels"],
            "context_labels": fallback["context_labels"],
            "behavior_labels": fallback["behavior_labels"],
            "intervention_labels": fallback["intervention_labels"],
        }

    extraction_conf = state.get("extraction_confidence", 0.0) or 0.0
    overall_conf = round((0.6 * extraction_conf) + (0.4 * norm_conf), 2)

    if overall_conf >= 0.85:
        note = "High confidence in both debrief extraction and memory normalization."
    elif overall_conf >= 0.65:
        note = "Moderate confidence in debrief interpretation; review if needed."
    else:
        note = "Lower confidence in debrief interpretation; parent review may be helpful."

    return {
        **state,
        **labels,
        "normalization_source": norm_source,
        "normalization_confidence": norm_conf,
        "normalization_reasoning": norm_reason,
        "debrief_overall_confidence": overall_conf,
        "debrief_confidence_note": note,
    }