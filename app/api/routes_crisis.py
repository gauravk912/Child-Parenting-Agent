from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.graph.builder import build_crisis_graph
from app.models.child import Child
from app.models.user import User
from app.schemas.crisis import (
    CrisisRequest,
    CrisisResponse,
    CrisisEvidenceSource,
    CrisisProvenance,
    CrisisTherapistSnippet,
    RankedIntervention,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crisis", tags=["crisis"])

crisis_graph = build_crisis_graph()


@router.post("/respond", response_model=CrisisResponse, status_code=status.HTTP_200_OK)
def respond_to_crisis(
    payload: CrisisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Crisis request received for child_id=%s", payload.child_id)

    child = (
        db.query(Child)
        .filter(Child.id == payload.child_id, Child.parent_id == current_user.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    try:
        result = crisis_graph.invoke(
            {
                "child_id": payload.child_id,
                "parent_message": payload.parent_message,
            }
        )

        logger.info("Crisis response generated successfully for child_id=%s", payload.child_id)

        return CrisisResponse(
            child_id=payload.child_id,
            child_name=result.get("child_name"),
            route=result.get("route", "crisis"),
            severity=result.get("severity", "moderate"),
            needs_emergency_support=result.get("needs_emergency_support", False),
            immediate_actions=result.get("immediate_actions", []),
            response_text=result.get("response_text", ""),
            evidence_sources=[
                CrisisEvidenceSource(**src) for src in result.get("evidence_sources", [])
            ],
            therapist_note_snippets=[
                CrisisTherapistSnippet(**{
                    "document_id": src.get("document_id"),
                    "title": src.get("title"),
                    "chunk_text": src.get("chunk_text"),
                    "score": src.get("score", 0.0),
                })
                for src in result.get("therapist_note_snippets", [])
            ],
            memory_summary=result.get("memory_summary"),
            recurring_contexts=result.get("recurring_contexts", []),
            prior_helpful_interventions=result.get("prior_helpful_interventions", []),
            ranked_interventions=[
                RankedIntervention(**item) for item in result.get("ranked_interventions", [])
            ],
            provenance=CrisisProvenance(
                used_child_profile=result.get("used_child_profile", False),
                used_graph_memory=result.get("used_graph_memory", False),
                used_tavily_evidence=result.get("used_tavily_evidence", False),
                used_therapist_notes=result.get("used_therapist_notes", False),
                used_llm_generation=result.get("used_llm_generation", False),
                safety_guard_applied=result.get("safety_guard_applied", False),
                provenance_summary=result.get("provenance_summary"),
            ),
        )
    except Exception as e:
        logger.exception("Crisis flow failed for child_id=%s", payload.child_id)
        raise HTTPException(
            status_code=500,
            detail=f"Crisis flow failed: {str(e)}"
        )