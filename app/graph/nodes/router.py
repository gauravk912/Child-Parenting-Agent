from app.services.llm_service import classify_crisis_structured


def _rule_based_router(state):
    message = state["parent_message"].lower()

    emergency_keywords = [
        "bleeding",
        "blood",
        "knife",
        "choking",
        "can't breathe",
        "cannot breathe",
        "not breathing",
        "seizure",
        "unconscious",
        "passed out",
        "hit head",
        "head injury",
        "ran into traffic",
        "jumped out",
        "overdose",
        "suicide",
        "kill myself",
        "kill himself",
        "kill herself",
    ]

    high_keywords = [
        "hitting",
        "biting",
        "throwing",
        "violent",
        "attacking",
        "hurting self",
        "hurting others",
        "breaking things",
        "unsafe",
        "ran away",
        "destroying",
    ]

    if any(keyword in message for keyword in emergency_keywords):
        return {
            **state,
            "route": "emergency",
            "severity": "emergency",
            "needs_emergency_support": True,
            "classification_source": "rule_fallback",
            "classification_confidence": 1.0,
            "classification_reasoning": "Emergency keyword match triggered hard safety override.",
        }

    if any(keyword in message for keyword in high_keywords):
        return {
            **state,
            "route": "crisis",
            "severity": "high",
            "needs_emergency_support": False,
            "classification_source": "rule_fallback",
            "classification_confidence": 0.9,
            "classification_reasoning": "High-risk keyword match triggered high severity.",
        }

    return {
        **state,
        "route": "crisis",
        "severity": "moderate",
        "needs_emergency_support": False,
        "classification_source": "rule_fallback",
        "classification_confidence": 0.7,
        "classification_reasoning": "No emergency/high keywords detected, defaulting to moderate.",
    }


def router(state):
    # Hard emergency override remains rule-based
    hard_override = _rule_based_router(state)
    if hard_override["severity"] == "emergency":
        return hard_override

    try:
        llm_result = classify_crisis_structured(
            child_name=state.get("child_name"),
            parent_message=state["parent_message"],
        )

        route = llm_result.get("route", "crisis")
        severity = llm_result.get("severity", "moderate")
        needs_emergency_support = llm_result.get("needs_emergency_support", False)

        if severity not in {"moderate", "high", "emergency"}:
            severity = "moderate"
        if route not in {"crisis", "emergency"}:
            route = "crisis"

        return {
            **state,
            "route": route,
            "severity": severity,
            "needs_emergency_support": bool(needs_emergency_support),
            "classification_source": "llm",
            "classification_confidence": llm_result.get("confidence", 0.0),
            "classification_reasoning": llm_result.get("reasoning_summary"),
        }

    except Exception:
        return _rule_based_router(state)