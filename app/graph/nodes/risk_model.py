# from app.db.session import SessionLocal
# from app.models.child import Child
# from app.services.weather_service import get_weather_context
# from app.services.calendar_service import get_calendar_context
# from app.services.risk_service import compute_daily_risk


# def risk_model(state):
#     db = SessionLocal()
#     try:
#         child = db.query(Child).filter(Child.id == state["child_id"]).first()
#         if not child:
#             raise ValueError("Child not found for prediction flow.")

#         weather = get_weather_context(location_query=state.get("location_query"))
#         calendar = get_calendar_context()

#         risk_score, risk_level, risk_factors = compute_daily_risk(
#             sensory_triggers=child.sensory_triggers,
#             calming_strategies=child.calming_strategies,
#             school_notes=child.school_notes,
#             medical_notes=child.medical_notes,
#             weather_risk_factors=weather.get("weather_risk_factors", []),
#             calendar_risk_factors=calendar.get("calendar_risk_factors", []),
#         )

#         return {
#             **state,
#             "child_name": child.name,
#             "sensory_triggers": child.sensory_triggers,
#             "calming_strategies": child.calming_strategies,
#             "school_notes": child.school_notes,
#             "medical_notes": child.medical_notes,
#             "weather_summary": weather.get("weather_summary"),
#             "weather_risk_factors": weather.get("weather_risk_factors", []),
#             "calendar_summary": calendar.get("calendar_summary"),
#             "calendar_risk_factors": calendar.get("calendar_risk_factors", []),
#             "risk_score": risk_score,
#             "risk_level": risk_level,
#             "risk_factors": risk_factors,
#         }
#     finally:
#         db.close()


from app.db.session import SessionLocal
from app.models.child import Child
from app.services.weather_service import get_weather_context
from app.services.calendar_service import get_calendar_context
from app.services.risk_service import compute_daily_risk


def risk_model(state):
    db = SessionLocal()
    try:
        child = db.query(Child).filter(Child.id == state["child_id"]).first()
        if not child:
            raise ValueError("Child not found for prediction flow.")

        weather = get_weather_context(location_query=state.get("location_query"))
        calendar = get_calendar_context(prediction_date=state.get("prediction_date"))

        risk_score, risk_level, risk_factors = compute_daily_risk(
            sensory_triggers=child.sensory_triggers,
            calming_strategies=child.calming_strategies,
            school_notes=child.school_notes,
            medical_notes=child.medical_notes,
            weather_risk_factors=weather.get("weather_risk_factors", []),
            calendar_risk_factors=calendar.get("calendar_risk_factors", []),
        )

        return {
            **state,
            "child_name": child.name,
            "sensory_triggers": child.sensory_triggers,
            "calming_strategies": child.calming_strategies,
            "school_notes": child.school_notes,
            "medical_notes": child.medical_notes,
            "weather_summary": weather.get("weather_summary"),
            "weather_risk_factors": weather.get("weather_risk_factors", []),
            "calendar_summary": calendar.get("calendar_summary"),
            "calendar_risk_factors": calendar.get("calendar_risk_factors", []),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
        }
    finally:
        db.close()