def safety_guard(state):
    message = state["parent_message"].lower()
    response_text = state.get("response_text", "")

    emergency_phrases = [
        "can't breathe",
        "cannot breathe",
        "not breathing",
        "seizure",
        "unconscious",
        "bleeding",
        "blood",
        "ran into traffic",
        "knife",
        "hit head",
        "head injury",
    ]

    safety_guard_applied = True

    if any(phrase in message for phrase in emergency_phrases):
        state["needs_emergency_support"] = True
        state["severity"] = "emergency"
        state["route"] = "emergency"

        emergency_suffix = (
            " This situation may require emergency services or urgent in-person support immediately."
        )

        if emergency_suffix.strip() not in response_text:
            response_text += emergency_suffix

    banned_phrases = [
        "punish",
        "punishment",
        "threaten",
        "shame",
        "force compliance",
    ]

    lowered = response_text.lower()
    for phrase in banned_phrases:
        if phrase in lowered:
            response_text = (
                "Focus on immediate safety, reducing stimulation, and using calm supportive regulation strategies. "
                "If the situation becomes physically unsafe, seek urgent in-person help."
            )
            break

    state["response_text"] = response_text
    state["safety_guard_applied"] = safety_guard_applied
    return state