from app.db.session import SessionLocal
from app.models.child import Child


def context_fetch(state):
    db = SessionLocal()
    try:
        child = db.query(Child).filter(Child.id == state["child_id"]).first()

        if not child:
            return {
                **state,
                "child_name": None,
                "nickname": None,
                "sensory_triggers": None,
                "calming_strategies": None,
                "school_notes": None,
                "medical_notes": None,
            }

        return {
            **state,
            "child_name": child.name,
            "nickname": child.nickname,
            "sensory_triggers": child.sensory_triggers,
            "calming_strategies": child.calming_strategies,
            "school_notes": child.school_notes,
            "medical_notes": child.medical_notes,
        }
    finally:
        db.close()