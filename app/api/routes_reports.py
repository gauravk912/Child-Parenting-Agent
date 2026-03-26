import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.graph.builder import build_report_graph
from app.models.child import Child
from app.models.user import User
from app.schemas.report import WeeklyReportRequest, WeeklyReportResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

report_graph = build_report_graph()


@router.post("/weekly", response_model=WeeklyReportResponse, status_code=status.HTTP_200_OK)
def generate_weekly_report(
    payload: WeeklyReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info("Weekly report request received for child_id=%s days=%s", payload.child_id, payload.days)

    child = (
        db.query(Child)
        .filter(Child.id == payload.child_id, Child.parent_id == current_user.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    try:
        result = report_graph.invoke(
            {
                "child_id": payload.child_id,
                "days": payload.days,
            }
        )

        logger.info("Weekly report generated successfully for child_id=%s", payload.child_id)

        return WeeklyReportResponse(
            child_id=payload.child_id,
            child_name=result.get("child_name"),
            days=payload.days,
            incident_count=result.get("incident_count", 0),
            top_antecedents=result.get("top_antecedents", []),
            top_behaviors=result.get("top_behaviors", []),
            top_consequences=result.get("top_consequences", []),
            top_interventions=result.get("top_interventions", []),
            latest_risk_level=result.get("latest_risk_level"),
            average_risk_score=result.get("average_risk_score"),
            summary_text=result.get("summary_text", ""),
            next_week_recommendations=result.get("next_week_recommendations", []),
            confidence_note=result.get("confidence_note"),
        )
    except Exception as e:
        logger.exception("Weekly report generation failed for child_id=%s", payload.child_id)
        raise HTTPException(
            status_code=500,
            detail=f"Weekly report flow failed: {str(e)}"
        )