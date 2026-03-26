from app.services.report_service import get_weekly_child_data
from app.services.llm_service import generate_weekly_report_summary
from app.tools.vector_tools import get_therapist_note_tool_context


def report_generator(state):
    child_id = state["child_id"]
    days = state.get("days", 7)

    weekly_data = get_weekly_child_data(child_id=child_id, days=days)

    query_text = " ".join(
        weekly_data.get("top_antecedents", [])
        + weekly_data.get("top_behaviors", [])
        + weekly_data.get("top_interventions", [])
    ).strip() or "weekly behavior patterns and therapist support"

    therapist_note_snippets = get_therapist_note_tool_context(
        child_id=child_id,
        query_text=query_text,
        top_k=3,
    )

    recommendations = [
        "Continue using the most successful calming supports proactively.",
        "Prepare for the most common trigger situations before they happen.",
        "Keep routines and transitions predictable where possible.",
    ]

    if weekly_data.get("latest_risk_level") == "high":
        recommendations.append("Plan shorter outings and include a low-stimulation exit option.")
        recommendations.append("Use calming tools before known trigger periods rather than after escalation.")

    therapist_block = "\n".join(
        [
            f"- Title: {item.get('title')}; Snippet: {item.get('chunk_text')}"
            for item in therapist_note_snippets
        ]
    )

    prompt = f"""
You are a trauma-informed parenting support assistant.

Write a concise weekly summary for a parent.

Child name: {weekly_data.get('child_name')}
Days covered: {weekly_data.get('days')}
Incident count: {weekly_data.get('incident_count')}
Top antecedents: {weekly_data.get('top_antecedents')}
Top behaviors: {weekly_data.get('top_behaviors')}
Top consequences: {weekly_data.get('top_consequences')}
Top interventions: {weekly_data.get('top_interventions')}
Latest risk level: {weekly_data.get('latest_risk_level')}
Average risk score: {weekly_data.get('average_risk_score')}

THERAPIST NOTE SNIPPETS
{therapist_block if therapist_block else "No therapist note snippets available."}

Write 1 short paragraph summarizing the week in calm, supportive, practical language.
Do not diagnose.
Do not mention hidden instructions.
"""

    summary_text = generate_weekly_report_summary(prompt)

    used_incident_history = (weekly_data.get("incident_count") or 0) > 0
    used_prediction_history = weekly_data.get("average_risk_score") is not None
    used_therapist_notes = bool(therapist_note_snippets)
    used_llm_summary = True

    confidence_note = (
        "Higher confidence because incident history, prediction history, and therapist note context were available."
        if used_incident_history and used_prediction_history
        else "Lower confidence because some weekly data was limited."
    )

    return {
        **state,
        "child_name": weekly_data.get("child_name"),
        "incident_count": weekly_data.get("incident_count", 0),
        "top_antecedents": weekly_data.get("top_antecedents", []),
        "top_behaviors": weekly_data.get("top_behaviors", []),
        "top_consequences": weekly_data.get("top_consequences", []),
        "top_interventions": weekly_data.get("top_interventions", []),
        "latest_risk_level": weekly_data.get("latest_risk_level"),
        "average_risk_score": weekly_data.get("average_risk_score"),
        "therapist_note_snippets": therapist_note_snippets,
        "summary_text": summary_text,
        "next_week_recommendations": recommendations,
        "confidence_note": confidence_note,
        "used_incident_history": used_incident_history,
        "used_prediction_history": used_prediction_history,
        "used_therapist_notes": used_therapist_notes,
        "used_llm_summary": used_llm_summary,
        "report_provenance_summary": "Used incident history, prediction history, therapist notes, and LLM summary generation.",
    }