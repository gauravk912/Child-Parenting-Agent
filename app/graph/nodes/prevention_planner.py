def prevention_planner(state):
    prevention_steps = [
        "Review the child's calming tools before the day becomes busy.",
        "Use short transition warnings before major schedule changes.",
        "Keep one preferred calming item easily available.",
    ]

    if state.get("risk_level") == "moderate":
        prevention_steps.extend([
            "Reduce unnecessary stimulation during errands or crowded transitions.",
            "Build in one quiet reset break after school.",
        ])

    if state.get("risk_level") == "high":
        prevention_steps.extend([
            "Pre-plan a low-stimulation escape option for busy environments.",
            "Shorten optional outings if early signs of overwhelm appear.",
            "Coordinate calming support before known trigger periods.",
        ])

    calming = state.get("calming_strategies")
    if calming:
        prevention_steps.append(f"Use known calming strategies proactively: {calming}.")

    return {
        **state,
        "prevention_steps": prevention_steps,
    }