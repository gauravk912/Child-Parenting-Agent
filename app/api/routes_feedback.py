import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.child import Child
from app.schemas.feedback import (
    InterventionFeedbackRequest,
    InterventionFeedbackResponse,
)
from app.services.feedback_service import save_intervention_feedback

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/intervention", response_model=InterventionFeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_intervention_feedback(
    payload: InterventionFeedbackRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    child = (
        db.query(Child)
        .filter(Child.id == payload.child_id, Child.parent_id == current_user.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    record = save_intervention_feedback(
        db=db,
        child_id=payload.child_id,
        intervention_name=payload.intervention_name,
        effectiveness_label=payload.effectiveness_label,
        context_note=payload.context_note,
        feedback_note=payload.feedback_note,
    )
 
    return InterventionFeedbackResponse(
        feedback_id=record.id,
        child_id=record.child_id,
        intervention_name=record.intervention_name,
        effectiveness_label=record.effectiveness_label,
        effectiveness_score=record.effectiveness_score,
        context_note=record.context_note,
        feedback_note=record.feedback_note,
        created_at=record.created_at,
    )