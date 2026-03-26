from app.services.report_service import generate_weekly_report
from app.db.session import SessionLocal


def report_generator(state):
    child_id = state["child_id"]
    days = state.get("days", 7)
    view_type = state.get("view_type", "parent")

    db = SessionLocal()
    try:
        result = generate_weekly_report(
            db=db,
            child_id=child_id,
            days=days,
            view_type=view_type,
        )

        return {
            **state,
            "child_name": result.get("child_name"),
            "incident_count": result.get("incident_count", 0),
            "top_antecedents": result.get("top_antecedents", []),
            "top_behaviors": result.get("top_behaviors", []),
            "top_consequences": result.get("top_consequences", []),
            "top_interventions": result.get("top_interventions", []),
            "latest_risk_level": result.get("latest_risk_level"),
            "average_risk_score": result.get("average_risk_score"),
            "therapist_note_snippets": result.get("therapist_note_snippets", []),
            "summary_text": result.get("summary_text", ""),
            "next_week_recommendations": result.get("next_week_recommendations", []),
            "confidence_note": result.get("confidence_note"),
            "used_incident_history": True,
            "used_prediction_history": True,
            "used_therapist_notes": bool(result.get("therapist_note_snippets")),
            "used_llm_summary": True,
            "report_provenance_summary": "Used incident history, prediction history, therapist notes, and LLM summary generation.",
        }
    finally:
        db.close()