from typing import List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field


TimelineItemType = Literal["incident", "prediction", "notification"]


class TimelineItem(BaseModel):
    item_type: TimelineItemType
    item_id: str
    timestamp: str
    title: str
    summary: str
    metadata: dict = Field(default_factory=dict)


class ChildTimelineResponse(BaseModel):
    child_id: UUID
    child_name: Optional[str] = None
    days: int
    item_count: int
    items: List[TimelineItem] = Field(default_factory=list)