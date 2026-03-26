import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.child import Child
from app.schemas.analytics import ChildAnalyticsResponse, AnalyticsRiskPoint
from app.services.analytics_service import build_child_analytics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/child/{child_id}", response_model=ChildAnalyticsResponse, status_code=status.HTTP_200_OK)
def get_child_analytics(
    child_id: UUID,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    child = (
        db.query(Child)
        .filter(Child.id == child_id, Child.parent_id == current_user.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    result = build_child_analytics(db=db, child_id=child_id, days=days)

    return ChildAnalyticsResponse(
        child_id=child_id,
        child_name=result.get("child_name"),
        days=result.get("days", days),
        incident_count=result.get("incident_count", 0),
        prediction_count=result.get("prediction_count", 0),
        therapist_note_count=result.get("therapist_note_count", 0),
        top_antecedents=result.get("top_antecedents", []),
        top_behaviors=result.get("top_behaviors", []),
        top_interventions=result.get("top_interventions", []),
        positive_feedback_interventions=result.get("positive_feedback_interventions", []),
        risk_level_distribution=result.get("risk_level_distribution", {}),
        average_risk_score=result.get("average_risk_score"),
        risk_trend_points=[
            AnalyticsRiskPoint(**p) for p in result.get("risk_trend_points", [])
        ],
        recurring_contexts=result.get("recurring_contexts", []),
    )