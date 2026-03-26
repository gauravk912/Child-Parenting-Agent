from app.db.session import SessionLocal
from app.models.child import Child
from app.services.incident_service import create_incident_with_abc


def sql_persist(state):
    db = SessionLocal()
    try:
        child = db.query(Child).filter(Child.id == state["child_id"]).first()
        if not child:
            raise ValueError("Child not found for debrief persistence.")

        incident = create_incident_with_abc(
            db=db,
            child_id=state["child_id"],
            parent_summary=state["parent_summary"],
            transcript_text=state.get("transcript_text"),
            location=state.get("location"),
            outcome_notes=state.get("outcome_notes"),
            antecedent=state.get("antecedent"),
            behavior=state.get("behavior"),
            consequence=state.get("consequence"),
            interventions_tried=state.get("interventions_tried", []),
        )

        return {
            **state,
            "incident_id": incident.id,
            "created_at": incident.created_at,
            "child_name": child.name,
            "parent_id": child.parent_id,
        }
    finally:
        db.close()