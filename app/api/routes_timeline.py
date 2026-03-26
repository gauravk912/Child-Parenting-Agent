import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.child import Child
from app.schemas.timeline import ChildTimelineResponse, TimelineItem
from app.services.timeline_service import build_child_timeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.get("/child/{child_id}", response_model=ChildTimelineResponse, status_code=status.HTTP_200_OK)
def get_child_timeline(
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

    result = build_child_timeline(db=db, child_id=child_id, days=days)

    return ChildTimelineResponse(
        child_id=child_id,
        child_name=result.get("child_name"),
        days=result.get("days", days),
        item_count=result.get("item_count", 0),
        items=[TimelineItem(**item) for item in result.get("items", [])],
    )