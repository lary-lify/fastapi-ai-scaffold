from fastapi import APIRouter

from Base.config.setting import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok", "service": settings.app.name, "env": settings.app.env}
