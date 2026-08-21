from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return a lightweight application health response."""
    settings = get_settings()
    return {"status": "ok", "environment": settings.app_env}
