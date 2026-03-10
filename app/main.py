from fastapi import FastAPI
from app.api.routes_health import router as health_router
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


@app.get("/")
def root():
    return {
        "message": "TinyTriggers backend is running",
        "environment": settings.app_env,
        "version": APP_VERSION
    }