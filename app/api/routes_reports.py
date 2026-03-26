import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.child import Child
from app.schemas.report import (
    WeeklyReportRequest,
    WeeklyReportResponse,
    WeeklyReportTherapistSnippet,
    ReportProvenance,
)
from app.services.report_service import generate_weekly_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/weekly", response_model=WeeklyReportResponse, status_code=status.HTTP_200_OK)
def generate_weekly_child_report(
    payload: WeeklyReportRequest,
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

    try:
        result = generate_weekly_report(
            db=db,
            child_id=payload.child_id,
            days=payload.days,
            view_type=payload.view_type,
        )

        return WeeklyReportResponse(
            child_id=payload.child_id,
            child_name=result.get("child_name"),
            days=payload.days,
            view_type=payload.view_type,
            incident_count=result.get("incident_count", 0),
            top_antecedents=result.get("top_antecedents", []),
            top_behaviors=result.get("top_behaviors", []),
            top_consequences=result.get("top_consequences", []),
            top_interventions=result.get("top_interventions", []),
            latest_risk_level=result.get("latest_risk_level"),
            average_risk_score=result.get("average_risk_score"),
            therapist_note_snippets=[
                WeeklyReportTherapistSnippet(**{
                    "document_id": x.get("document_id"),
                    "title": x.get("title"),
                    "chunk_text": x.get("chunk_text"),
                    "score": x.get("score", 0.0),
                })
                for x in result.get("therapist_note_snippets", [])
            ],
            summary_text=result.get("summary_text", ""),
            next_week_recommendations=result.get("next_week_recommendations", []),
            confidence_note=result.get("confidence_note"),
            structured_flags=result.get("structured_flags", {}),
            provenance=ReportProvenance(
                used_incident_history=True,
                used_prediction_history=True,
                used_therapist_notes=bool(result.get("therapist_note_snippets")),
                used_llm_summary=True,
                provenance_summary="Used incident history, prediction history, therapist notes, and LLM summary generation.",
            ),
        )
    except Exception as e:
        logger.exception("Weekly report flow failed for child_id=%s", payload.child_id)
        raise HTTPException(
            status_code=500,
            detail=f"Weekly report flow failed: {str(e)}"
        )