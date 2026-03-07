from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.app_env
    }


@router.get("/ready")
def readiness_check():
    return {
        "status": "ready"
    }