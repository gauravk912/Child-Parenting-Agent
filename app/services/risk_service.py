from typing import Dict, List, Tuple


def build_prediction_features(
    sensory_triggers: str | None,
    calming_strategies: str | None,
    school_notes: str | None,
    medical_notes: str | None,
    weather_summary: str | None,
    weather_risk_factors: List[str],
    calendar_summary: str | None,
    calendar_risk_factors: List[str],
) -> Dict:
    features = {
        "has_sensory_trigger_profile": bool(sensory_triggers),
        "has_calming_strategies": bool(calming_strategies),
        "has_school_risk_context": bool(school_notes),
        "has_medical_context": bool(medical_notes),
        "weather_risk_count": len(weather_risk_factors),
        "calendar_risk_count": len(calendar_risk_factors),
        "is_transition_heavy_day": False,
        "has_appointment_day": False,
        "has_outing_risk": False,
        "has_routine_anchor": False,
    }

    lowered_calendar = (calendar_summary or "").lower()

    if "school drop-off" in lowered_calendar or "therapy" in lowered_calendar or "appointment" in lowered_calendar:
        features["is_transition_heavy_day"] = True

    if "appointment" in lowered_calendar or "therapy" in lowered_calendar:
        features["has_appointment_day"] = True

    if "errand" in lowered_calendar or "shopping" in lowered_calendar or "visit" in lowered_calendar:
        features["has_outing_risk"] = True

    if "routine" in lowered_calendar or "wind-down" in lowered_calendar:
        features["has_routine_anchor"] = True

    return features


def compute_daily_risk(
    sensory_triggers: str | None,
    calming_strategies: str | None,
    school_notes: str | None,
    medical_notes: str | None,
    weather_summary: str | None,
    weather_risk_factors: List[str],
    calendar_summary: str | None,
    calendar_risk_factors: List[str],
) -> Tuple[float, str, List[str], Dict]:
    features = build_prediction_features(
        sensory_triggers=sensory_triggers,
        calming_strategies=calming_strategies,
        school_notes=school_notes,
        medical_notes=medical_notes,
        weather_summary=weather_summary,
        weather_risk_factors=weather_risk_factors,
        calendar_summary=calendar_summary,
        calendar_risk_factors=calendar_risk_factors,
    )

    risk_score = 0.15
    risk_factors: List[str] = []

    if features["has_sensory_trigger_profile"]:
        risk_score += 0.18
        risk_factors.append(f"Known sensory triggers: {sensory_triggers}")

    if features["has_school_risk_context"]:
        risk_score += 0.10
        risk_factors.append(f"School-related context: {school_notes}")

    if features["has_medical_context"]:
        risk_score += 0.08
        risk_factors.append(f"Medical considerations: {medical_notes}")

    if weather_risk_factors:
        risk_score += min(0.12, 0.04 * len(weather_risk_factors))
        risk_factors.extend(weather_risk_factors)

    if calendar_risk_factors:
        risk_score += min(0.22, 0.05 * len(calendar_risk_factors))
        risk_factors.extend(calendar_risk_factors)

    if features["is_transition_heavy_day"]:
        risk_score += 0.10
        risk_factors.append("Prediction feature: today appears transition-heavy.")

    if features["has_appointment_day"]:
        risk_score += 0.05
        risk_factors.append("Prediction feature: appointment or therapy may add stress.")

    if features["has_outing_risk"]:
        risk_score += 0.07
        risk_factors.append("Prediction feature: outing or errand context may add sensory load.")

    if features["has_routine_anchor"]:
        risk_score -= 0.04
        risk_factors.append("Prediction feature: a routine anchor may help regulation later in the day.")

    if features["has_calming_strategies"]:
        risk_score -= 0.05

    risk_score = max(0.0, min(1.0, round(risk_score, 2)))

    if risk_score >= 0.75:
        risk_level = "high"
    elif risk_score >= 0.45:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return risk_score, risk_level, risk_factors, features