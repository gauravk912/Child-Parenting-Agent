from app.services.llm_service import extract_debrief_structured


def _heuristic_extract(state, text: str, parent_summary: str):
    antecedent = None
    behavior = None
    consequence = None

    trigger_words = ["before", "when", "after school", "transition", "loud", "crowded", "asked to", "told to"]
    behavior_words = ["screamed", "crying", "throwing", "hitting", "biting", "ran", "fell", "kicked", "yelling", "dropped to the floor"]
    consequence_words = ["then", "afterwards", "finally", "calmed", "settled", "slept", "stopped", "hugged", "slowed down"]

    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]

    for sentence in sentences:
        s = sentence.lower()

        if antecedent is None and any(word in s for word in trigger_words):
            antecedent = sentence

        if behavior is None and any(word in s for word in behavior_words):
            behavior = sentence

        if consequence is None and any(word in s for word in consequence_words):
            consequence = sentence

    if antecedent is None and parent_summary:
        antecedent = parent_summary

    if behavior is None and parent_summary:
        behavior = parent_summary

    if consequence is None:
        consequence = state.get("outcome_notes") or None

    return antecedent, behavior, consequence


def abc_extractor(state):
    raw_text = state.get("raw_text", "").strip()
    parent_summary = state.get("parent_summary", "").strip()

    text = raw_text if raw_text else parent_summary

    try:
        llm_result = extract_debrief_structured(text)

        antecedent = llm_result.get("antecedent")
        behavior = llm_result.get("behavior")
        consequence = llm_result.get("consequence")

        # Safety fallback if LLM returns too little
        if not antecedent and not behavior and not consequence:
            raise ValueError("LLM extraction returned no usable fields.")

        extraction_source = "llm"
        extraction_confidence = llm_result.get("confidence", 0.0)
        extraction_reasoning = llm_result.get("reasoning_summary")

    except Exception:
        antecedent, behavior, consequence = _heuristic_extract(state, text, parent_summary)
        extraction_source = "heuristic_fallback"
        extraction_confidence = 0.5
        extraction_reasoning = "Rule-based heuristic fallback used."

    missing_fields = []
    if not antecedent:
        missing_fields.append("antecedent")
    if not behavior:
        missing_fields.append("behavior")
    if not consequence:
        missing_fields.append("consequence")
    if not state.get("interventions_tried"):
        missing_fields.append("interventions_tried")
    if not state.get("location"):
        missing_fields.append("location")

    follow_up_question = None
    if missing_fields:
        if "antecedent" in missing_fields:
            follow_up_question = "What happened right before your child became upset?"
        elif "behavior" in missing_fields:
            follow_up_question = "What exactly did your child do during the incident?"
        elif "consequence" in missing_fields:
            follow_up_question = "How did the incident end, or what happened after?"
        elif "interventions_tried" in missing_fields:
            follow_up_question = "What calming strategies or interventions did you try?"
        elif "location" in missing_fields:
            follow_up_question = "Where did the incident happen?"

    debrief_quality = "complete" if not missing_fields else "partial"

    return {
        **state,
        "antecedent": antecedent,
        "behavior": behavior,
        "consequence": consequence,
        "missing_fields": missing_fields,
        "follow_up_question": follow_up_question,
        "debrief_quality": debrief_quality,
        "extraction_source": extraction_source,
        "extraction_confidence": extraction_confidence,
        "extraction_reasoning": extraction_reasoning,
    }