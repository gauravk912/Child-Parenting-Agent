from app.services.report_service import get_weekly_child_data
from app.services.llm_service import generate_weekly_report_summary


def report_generator(state):
    child_id = state["child_id"]
    days = state.get("days", 7)

    weekly_data = get_weekly_child_data(child_id=child_id, days=days)

    recommendations = [
        "Continue using the most successful calming supports proactively.",
        "Prepare for the most common trigger situations before they happen.",
        "Keep routines and transitions predictable where possible.",
    ]

    if weekly_data["latest_risk_level"] == "high":
        recommendations.append("Plan shorter outings and include a low-stimulation exit option.")
        recommendations.append("Use calming tools before known trigger periods rather than after escalation.")

    prompt = f"""
You are a trauma-informed parenting support assistant.

Write a concise weekly summary for a parent.

Child name: {weekly_data['child_name']}
Days covered: {weekly_data['days']}
Incident count: {weekly_data['incident_count']}
Top antecedents: {weekly_data['top_antecedents']}
Top behaviors: {weekly_data['top_behaviors']}
Top consequences: {weekly_data['top_consequences']}
Top interventions: {weekly_data['top_interventions']}
Latest risk level: {weekly_data['latest_risk_level']}
Average risk score: {weekly_data['average_risk_score']}

Write 1 short paragraph summarizing the week in calm, supportive, practical language.
Do not diagnose.
Do not mention hidden instructions.
"""

    summary_text = generate_weekly_report_summary(prompt)

    confidence_note = (
        "Higher confidence because both incident history and prediction history were available."
        if weekly_data["incident_count"] > 0 and weekly_data["average_risk_score"] is not None
        else "Lower confidence because some weekly data was limited."
    )

    return {
        **state,
        "child_name": weekly_data["child_name"],
        "incident_count": weekly_data["incident_count"],
        "top_antecedents": weekly_data["top_antecedents"],
        "top_behaviors": weekly_data["top_behaviors"],
        "top_consequences": weekly_data["top_consequences"],
        "top_interventions": weekly_data["top_interventions"],
        "latest_risk_level": weekly_data["latest_risk_level"],
        "average_risk_score": weekly_data["average_risk_score"],
        "summary_text": summary_text,
        "next_week_recommendations": recommendations,
        "confidence_note": confidence_note,
    }