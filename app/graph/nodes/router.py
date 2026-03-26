def router(state):
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
        }

    if any(keyword in message for keyword in high_keywords):
        return {
            **state,
            "route": "crisis",
            "severity": "high",
            "needs_emergency_support": False,
        }

    return {
        **state,
        "route": "crisis",
        "severity": "moderate",
        "needs_emergency_support": False,
    }