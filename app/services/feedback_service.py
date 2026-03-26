from typing import Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.intervention import Intervention


def map_effectiveness_to_score(label: str) -> float:
    label = label.strip().lower()
    if label == "helpful":
        return 1.0
    if label == "partial":
        return 0.5
    return 0.0


def save_intervention_feedback(
    db: Session,
    child_id: UUID,
    intervention_name: str,
    effectiveness_label: str,
    context_note: str | None = None,
    feedback_note: str | None = None,
) -> Intervention:
    record = Intervention(
        child_id=child_id,
        intervention_name=intervention_name.strip(),
        effectiveness_label=effectiveness_label,
        effectiveness_score=map_effectiveness_to_score(effectiveness_label),
        context_note=context_note,
        feedback_note=feedback_note,
    )

    db.add(record)
    db.commit()
    db.refresh(record)
    return record