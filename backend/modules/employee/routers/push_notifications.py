"""push notifications router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/push-notifications")


@router.get("/push_notifications/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "push_notifications", "prefix": "/api/v1/push-notifications"}
