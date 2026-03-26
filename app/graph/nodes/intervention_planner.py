def intervention_planner(state):
    calming = state.get("calming_strategies")
    triggers = state.get("sensory_triggers")
    severity = state.get("severity", "moderate")

    actions = [
        "First make sure the child and everyone nearby is physically safe.",
        "Lower noise, lights, and extra stimulation if possible.",
        "Use a calm voice and short simple sentences.",
    ]

    if calming:
        actions.append(f"Try the child's known calming strategies: {calming}.")

    if triggers:
        actions.append(f"Watch for likely triggers such as: {triggers}.")

    if severity == "high":
        actions.append("Move nearby hard, sharp, or breakable objects away.")
        actions.append("Give the child space unless immediate safety requires intervention.")

    if severity == "emergency":
        actions = [
            "Call emergency services immediately if there is serious injury or immediate danger.",
            "Prioritize breathing, bleeding, head injury, or risk of severe harm first.",
            "Move dangerous objects away only if you can do it safely.",
            "Call another trusted adult nearby for immediate help if available.",
        ]

    return {
        **state,
        "immediate_actions": actions,
    }