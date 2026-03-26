from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_health import router as health_router
from app.api.routes_children import router as children_router
from app.api.routes_crisis import router as crisis_router
from app.api.routes_debrief import router as debrief_router
from app.api.routes_prediction import router as prediction_router
from app.api.routes_reports import router as reports_router
from app.core.config import settings
from app.core.constants import APP_VERSION
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title=settings.app_name,
    version=APP_VERSION,
    description="TinyTriggers backend for trauma-informed parenting support"
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(children_router)
app.include_router(crisis_router)
app.include_router(debrief_router)
app.include_router(prediction_router)
app.include_router(reports_router)


@app.get("/")
def root():
    return {
        "message": "TinyTriggers backend is running",
        "environment": settings.app_env,
        "version": APP_VERSION
    }