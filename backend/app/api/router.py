from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.weekly_indicators import router as weekly_indicators_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(jobs_router)
api_router.include_router(weekly_indicators_router)
