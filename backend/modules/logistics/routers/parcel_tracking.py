"""parcel tracking router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/parcel-tracking")


@router.get("/parcel_tracking/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "parcel_tracking", "prefix": "/api/v1/parcel-tracking"}
