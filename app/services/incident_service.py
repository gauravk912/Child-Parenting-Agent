from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.abc_record import ABCRecord
from app.models.intervention import Intervention
from app.models.prediction import Prediction

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.prediction import Prediction

def create_incident_with_abc(
    db: Session,
    child_id: UUID,
    parent_summary: str,
    transcript_text: Optional[str],
    location: Optional[str],
    outcome_notes: Optional[str],
    antecedent: Optional[str],
    behavior: Optional[str],
    consequence: Optional[str],
    interventions_tried: List[str],
) -> Incident:
    incident = Incident(
        child_id=child_id,
        summary=parent_summary,
        transcript_text=transcript_text,
        location=location,
        outcome_notes=outcome_notes,
    )
    db.add(incident)
    db.flush()

    abc_record = ABCRecord(
        incident_id=incident.id,
        antecedent=antecedent,
        behavior=behavior,
        consequence=consequence,
    )
    db.add(abc_record)

    for idx, intervention_name in enumerate(interventions_tried):
        db.add(
            Intervention(
                incident_id=incident.id,
                name=intervention_name,
                sort_order=idx,
            )
        )

    db.commit()
    db.refresh(incident)
    return incident


def create_daily_prediction(
    db: Session,
    child_id: UUID,
    prediction_date: str,
    risk_score: float,
    risk_level: str,
    weather_summary: str | None,
    calendar_summary: str | None,
    risk_factors: list[str],
    prevention_steps: list[str],
) -> Prediction:
    prediction = Prediction(
        child_id=child_id,
        prediction_date=datetime.fromisoformat(prediction_date).date(),
        risk_score=risk_score,
        risk_level=risk_level,
        weather_summary=weather_summary,
        calendar_summary=calendar_summary,
        risk_factors=json.dumps(risk_factors),
        prevention_steps=json.dumps(prevention_steps),
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction