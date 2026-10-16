"""Health endpoints.

Two endpoints, deliberately. They answer different questions and a platform
reacts to them differently:

  /health        liveness  -- "is this process wedged?"  Failure => restart me.
  /health/ready  readiness -- "can I serve a request now?" Failure => stop
                              sending me traffic, but do not restart me.

Liveness must NOT touch the database. If it did, a ten-second database blip
would fail the liveness probe on every replica at once and Kubernetes would
restart the entire backend -- turning a brief dependency hiccup into a full
outage.
"""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def liveness() -> dict[str, str]:
    """Process-only check. Returns 200 whenever the app can answer at all."""
    return {"status": "ok", "service": settings.app_name, "environment": settings.environment}


@router.get("/health/ready")
def readiness(response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    """Dependency check. 503 while the database is unreachable."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - any failure means "not ready"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "database": "unreachable", "detail": str(exc)[:200]}
    return {"status": "ready", "database": "ok"}
