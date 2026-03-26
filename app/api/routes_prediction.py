from datetime import date
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.db.session import SessionLocal
from app.graph.builder import build_prediction_graph
from app.models.child import Child
from app.models.user import User
from app.schemas.prediction import DailyPredictionRequest, DailyPredictionResponse
from app.services.incident_service import create_daily_prediction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prediction", tags=["prediction"])

prediction_graph = build_prediction_graph()


@router.post("/daily", response_model=DailyPredictionResponse, status_code=status.HTTP_200_OK)
def generate_daily_prediction(
    payload: DailyPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

        logger.info(
            "Prediction generated successfully for child_id=%s prediction_id=%s",
            payload.child_id,
            prediction.id,
        )

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