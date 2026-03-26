from typing import Dict, List, Tuple


def compute_daily_risk(
    sensory_triggers: str | None,
    calming_strategies: str | None,
    school_notes: str | None,
    medical_notes: str | None,
    weather_risk_factors: List[str],
    calendar_risk_factors: List[str],
) -> Tuple[float, str, List[str]]:
    risk_score = 0.20
    risk_factors: List[str] = []

    if sensory_triggers:
        risk_score += 0.20
        risk_factors.append(f"Known sensory triggers: {sensory_triggers}")

    if school_notes:
        risk_score += 0.10
        risk_factors.append(f"School-related context: {school_notes}")

    if medical_notes:
        risk_score += 0.10
        risk_factors.append(f"Medical considerations: {medical_notes}")

    if weather_risk_factors:
        risk_score += 0.10
        risk_factors.extend(weather_risk_factors)

    if calendar_risk_factors:
        risk_score += 0.20
        risk_factors.extend(calendar_risk_factors)

    if calming_strategies:
        risk_score -= 0.05

    risk_score = max(0.0, min(1.0, round(risk_score, 2)))

    if risk_score >= 0.75:
        risk_level = "high"
    elif risk_score >= 0.45:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return risk_score, risk_level, risk_factors