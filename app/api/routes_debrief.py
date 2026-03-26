from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.graph.builder import build_debrief_graph
from app.models.child import Child
from app.models.user import User
from app.schemas.debrief import DebriefRequest, DebriefResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debrief", tags=["debrief"])

debrief_graph = build_debrief_graph()


@router.post("/submit", response_model=DebriefResponse, status_code=status.HTTP_200_OK)
def submit_debrief(
    payload: DebriefRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Debrief request received for child_id=%s", payload.child_id)

    child = (
        db.query(Child)
        .filter(Child.id == payload.child_id, Child.parent_id == current_user.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    try:
        result = debrief_graph.invoke(
            {
                "child_id": payload.child_id,
                "parent_summary": payload.parent_summary,
                "transcript_text": payload.transcript_text,
                "location": payload.location,
                "interventions_tried": payload.interventions_tried,
                "outcome_notes": payload.outcome_notes,
                "graph_updated": False,
            }
        )

        logger.info(
            "Debrief processed successfully for child_id=%s incident_id=%s",
            payload.child_id,
            result.get("incident_id"),
        )

        return DebriefResponse(
            incident_id=result["incident_id"],
            child_id=payload.child_id,
            child_name=result.get("child_name"),
            antecedent=result.get("antecedent"),
            behavior=result.get("behavior"),
            consequence=result.get("consequence"),
            interventions_tried=result.get("interventions_tried", []),
            parent_summary=payload.parent_summary,
            transcript_text=payload.transcript_text,
            outcome_notes=payload.outcome_notes,
            location=payload.location,
            created_at=result.get("created_at"),
            graph_updated=result.get("graph_updated", False),
            debrief_quality=result.get("debrief_quality", "complete"),
            missing_fields=result.get("missing_fields", []),
            follow_up_question=result.get("follow_up_question"),
        )
    except Exception as e:
        logger.exception("Debrief flow failed for child_id=%s", payload.child_id)
        raise HTTPException(
            status_code=500,
            detail=f"Debrief flow failed: {str(e)}"
        )