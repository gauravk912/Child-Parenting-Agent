from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


class PredictionProvenance(BaseModel):
    used_child_profile: bool = False
    used_weather_tool: bool = False
    used_calendar_tool: bool = False
    used_feature_engineering: bool = False
    used_rule_based_risk_engine: bool = False
    provenance_summary: Optional[str] = None


class DailyPredictionRequest(BaseModel):
    child_id: UUID
    prediction_date: Optional[str] = Field(
        default=None,
        description="Optional date in YYYY-MM-DD format. If omitted, server uses today."
    )
    location_query: Optional[str] = Field(
        default=None,
        description="Optional location like 'Columbus,OH,US'. Falls back to default env location."
    )


class DailyPredictionResponse(BaseModel):
    prediction_id: UUID
    child_id: UUID
    child_name: Optional[str] = None

    prediction_date: str
    risk_score: float
    risk_level: str

    weather_summary: Optional[str] = None
    calendar_summary: Optional[str] = None

    risk_factors: List[str] = Field(default_factory=list)
    prevention_steps: List[str] = Field(default_factory=list)

    engineered_features: Dict[str, Any] = Field(default_factory=dict)

    notification_triggered: bool = False
    notification_message: Optional[str] = None

    provenance: PredictionProvenance

    created_at: Optional[datetime] = None