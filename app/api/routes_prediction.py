from datetime import date
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.db.session import SessionLocal
from app.graph.builder import build_prediction_graph
from app.models.child import Child
from app.schemas.prediction import (
    DailyPredictionRequest,
    DailyPredictionResponse,
    PredictionProvenance,
)
from app.services.incident_service import create_daily_prediction
from app.services.notification_service import (
    build_high_risk_notification,
    save_notification,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prediction", tags=["prediction"])

prediction_graph = build_prediction_graph()


@router.post("/daily", response_model=DailyPredictionResponse, status_code=status.HTTP_200_OK)
def generate_daily_prediction(
    payload: DailyPredictionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    logger.info("Prediction request received for child_id=%s", payload.child_id)

    child = (
        db.query(Child)
        .filter(Child.id == payload.child_id, Child.parent_id == current_user.id)
        .first()
    )
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    prediction_db = SessionLocal()
    try:
        prediction_date = payload.prediction_date or str(date.today())

        result = prediction_graph.invoke(
            {
                "child_id": payload.child_id,
                "prediction_date": prediction_date,
                "location_query": payload.location_query,
            }
        )

        prediction = create_daily_prediction(
            db=prediction_db,
            child_id=payload.child_id,
            prediction_date=prediction_date,
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            weather_summary=result.get("weather_summary"),
            calendar_summary=result.get("calendar_summary"),
            risk_factors=result.get("risk_factors", []),
            prevention_steps=result.get("prevention_steps", []),
        )

        notification_triggered = False
        notification_message = None

        if result.get("risk_score", 0.0) >= settings.notification_high_risk_threshold:
            notification = build_high_risk_notification(
                child_id=payload.child_id,
                child_name=result.get("child_name") or child.name,
                prediction_date=prediction_date,
                risk_score=result.get("risk_score", 0.0),
                prevention_steps=result.get("prevention_steps", []),
            )
            save_notification(notification)
            notification_triggered = True
            notification_message = notification["message"]

        used_ml_model = result.get("prediction_model_source") == "ml_model"

        return DailyPredictionResponse(
            prediction_id=prediction.id,
            child_id=payload.child_id,
            child_name=result.get("child_name"),
            prediction_date=prediction_date,
            risk_score=result.get("risk_score", 0.0),
            risk_level=result.get("risk_level", "low"),
            weather_summary=result.get("weather_summary"),
            calendar_summary=result.get("calendar_summary"),
            risk_factors=result.get("risk_factors", []),
            prevention_steps=result.get("prevention_steps", []),
            engineered_features=result.get("engineered_features", {}),
            prediction_model_source=result.get("prediction_model_source"),
            prediction_model_probability=result.get("prediction_model_probability"),
            prediction_confidence=result.get("prediction_confidence"),
            prediction_confidence_note=result.get("prediction_confidence_note"),
            notification_triggered=notification_triggered,
            notification_message=notification_message,
            provenance=PredictionProvenance(
                used_child_profile=True,
                used_weather_tool=True,
                used_calendar_tool=True,
                used_feature_engineering=True,
                used_ml_model=used_ml_model,
                used_rule_based_risk_engine=not used_ml_model,
                provenance_summary=(
                    "Used child profile, weather tool, calendar tool, feature engineering, and ML prediction model."
                    if used_ml_model
                    else "Used child profile, weather tool, calendar tool, feature engineering, and rule-based fallback risk engine."
                ),
            ),
            created_at=prediction.created_at,
        )
    except Exception as e:
        logger.exception("Prediction flow failed for child_id=%s", payload.child_id)
        raise HTTPException(
            status_code=500,
            detail=f"Prediction flow failed: {str(e)}"
        )
    finally:
        prediction_db.close()