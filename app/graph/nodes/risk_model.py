from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.child import Child
from app.models.incident import Incident
from app.services.weather_service import get_weather_context
from app.services.calendar_service import get_calendar_context
from app.services.prediction_model_service import predict_with_saved_model


def _compute_rule_based_score(engineered_features: dict) -> float:
    risk_score = 0.20

    if engineered_features["has_sensory_trigger_profile"]:
        risk_score += 0.10
    if engineered_features["has_school_risk_context"]:
        risk_score += 0.10
    if engineered_features["has_medical_context"]:
        risk_score += 0.05

    risk_score += min(0.15, 0.03 * engineered_features["weather_risk_count"])
    risk_score += min(0.25, 0.05 * engineered_features["calendar_risk_count"])

    if engineered_features["is_transition_heavy_day"]:
        risk_score += 0.08
    if engineered_features["has_appointment_day"]:
        risk_score += 0.05
    if engineered_features["has_outing_risk"]:
        risk_score += 0.07
    if engineered_features["has_routine_anchor"]:
        risk_score -= 0.03

    risk_score += min(0.12, 0.02 * engineered_features["recent_incident_count_7d"])
    risk_score += min(0.08, 0.02 * engineered_features["recent_incident_count_3d"])

    return max(0.0, min(round(risk_score, 2), 1.0))


def _derive_risk_level(score: float) -> str:
    if score >= 0.75:
        return "high"
    elif score >= 0.45:
        return "moderate"
    return "low"


def _build_prediction_confidence(
    model_source: str,
    ml_probability,
    rule_score: float,
    engineered_features: dict,
    weather_summary,
    calendar_summary,
):
    confidence = 0.45

    if engineered_features["recent_incident_count_7d"] > 0:
        confidence += 0.10
    if engineered_features["weather_risk_count"] > 0:
        confidence += 0.10
    if engineered_features["calendar_risk_count"] > 0:
        confidence += 0.15
    if engineered_features["is_transition_heavy_day"]:
        confidence += 0.05
    if engineered_features["has_outing_risk"]:
        confidence += 0.05

    if model_source == "ml_model":
        confidence += 0.10
        if ml_probability is not None:
            distance = abs(float(ml_probability) - 0.50)
            if distance >= 0.25:
                confidence += 0.05
    else:
        confidence += 0.05

    if weather_summary:
        confidence += 0.05
    if calendar_summary:
        confidence += 0.05

    confidence = min(round(confidence, 2), 0.95)

    if confidence >= 0.85:
        note = "High confidence because child history, live context, and prediction signals are all available."
    elif confidence >= 0.65:
        note = "Moderate confidence because prediction used a mix of recent history and available daily context."
    else:
        note = "Lower confidence because some context signals are limited or uncertain."

    return confidence, note


def risk_model(state):
    child_id = state["child_id"]
    prediction_date = state["prediction_date"]
    location_query = state.get("location_query")

    db: Session = SessionLocal()
    try:
        child = db.query(Child).filter(Child.id == child_id).first()
        if not child:
            raise ValueError("Child not found for prediction.")

        weather = get_weather_context(location_query=location_query) or {}
        calendar = get_calendar_context(prediction_date=prediction_date) or {}

        recent_incidents = db.query(Incident).filter(Incident.child_id == child_id).all()
        recent_count = len(recent_incidents)

        weather_risk_factors = weather.get("risk_factors", []) or []
        calendar_risk_factors = calendar.get("risk_factors", []) or []

        engineered_features = {
            "has_sensory_trigger_profile": bool(child.sensory_triggers),
            "has_calming_strategies": bool(child.calming_strategies),
            "has_school_risk_context": bool(child.school_notes),
            "has_medical_context": bool(child.medical_notes),
            "weather_risk_count": len(weather_risk_factors),
            "calendar_risk_count": len(calendar_risk_factors),
            "is_transition_heavy_day": any("transition" in x.lower() for x in calendar_risk_factors),
            "has_appointment_day": any("therapy" in x.lower() or "appointment" in x.lower() for x in calendar_risk_factors),
            "has_outing_risk": any(
                "outing" in x.lower()
                or "errand" in x.lower()
                or "store" in x.lower()
                or "shopping" in x.lower()
                or "visit" in x.lower()
                for x in calendar_risk_factors
            ),
            "has_routine_anchor": any("routine anchor" in x.lower() for x in calendar_risk_factors),
            "recent_incident_count_7d": float(min(recent_count, 7)),
            "recent_incident_count_3d": float(min(recent_count, 3)),
        }

        ml_feature_dict = {
            "has_sensory_trigger_profile": float(engineered_features["has_sensory_trigger_profile"]),
            "has_calming_strategies": float(engineered_features["has_calming_strategies"]),
            "has_school_risk_context": float(engineered_features["has_school_risk_context"]),
            "has_medical_context": float(engineered_features["has_medical_context"]),
            "recent_incident_count_7d": engineered_features["recent_incident_count_7d"],
            "recent_incident_count_3d": engineered_features["recent_incident_count_3d"],
            "calendar_risk_count": float(engineered_features["calendar_risk_count"]),
            "is_transition_heavy_day": float(engineered_features["is_transition_heavy_day"]),
            "has_appointment_day": float(engineered_features["has_appointment_day"]),
            "has_outing_risk": float(engineered_features["has_outing_risk"]),
            "has_routine_anchor": float(engineered_features["has_routine_anchor"]),
        }

        rule_score = _compute_rule_based_score(engineered_features)

        ml_probability, model_source = predict_with_saved_model(ml_feature_dict)

        prediction_model_source = "rule_fallback"
        prediction_model_probability = None
        final_score = rule_score

        if ml_probability is not None:
            prediction_model_probability = float(ml_probability)

            blended_score = round((0.65 * rule_score) + (0.35 * float(ml_probability)), 2)

            if rule_score >= 0.65 and blended_score < 0.45:
                final_score = max(0.45, round((rule_score + blended_score) / 2, 2))
            elif rule_score >= 0.45 and blended_score < 0.30:
                final_score = max(0.35, round((rule_score + blended_score) / 2, 2))
            else:
                final_score = blended_score

            prediction_model_source = "ml_model"

        risk_score = max(0.0, min(round(final_score, 2), 1.0))
        risk_level = _derive_risk_level(risk_score)

        prediction_confidence, prediction_confidence_note = _build_prediction_confidence(
            model_source=prediction_model_source,
            ml_probability=prediction_model_probability,
            rule_score=rule_score,
            engineered_features=engineered_features,
            weather_summary=weather.get("summary"),
            calendar_summary=calendar.get("summary"),
        )

        risk_factors = []
        if child.sensory_triggers:
            risk_factors.append(f"Known sensory triggers: {child.sensory_triggers}")
        if child.school_notes:
            risk_factors.append(f"School-related context: {child.school_notes}")
        if child.medical_notes:
            risk_factors.append(f"Medical considerations: {child.medical_notes}")

        risk_factors.extend(weather_risk_factors)
        risk_factors.extend(calendar_risk_factors)

        if engineered_features["is_transition_heavy_day"]:
            risk_factors.append("Prediction feature: today appears transition-heavy.")
        if engineered_features["has_appointment_day"]:
            risk_factors.append("Prediction feature: appointment or therapy may add stress.")
        if engineered_features["has_outing_risk"]:
            risk_factors.append("Prediction feature: outing or errand context may add sensory load.")
        if engineered_features["has_routine_anchor"]:
            risk_factors.append("Prediction feature: a routine anchor may help regulation later in the day.")
        if engineered_features["recent_incident_count_7d"] > 0:
            risk_factors.append("Prediction feature: recent incident history increases near-term risk.")

        return {
            **state,
            "child_name": child.name,
            "sensory_triggers": child.sensory_triggers,
            "calming_strategies": child.calming_strategies,
            "school_notes": child.school_notes,
            "medical_notes": child.medical_notes,
            "weather_summary": weather.get("summary"),
            "calendar_summary": calendar.get("summary"),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "engineered_features": engineered_features,
            "prediction_model_source": prediction_model_source,
            "prediction_model_probability": prediction_model_probability,
            "prediction_confidence": prediction_confidence,
            "prediction_confidence_note": prediction_confidence_note,
        }
    finally:
        db.close()