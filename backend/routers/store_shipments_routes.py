"""store shipments routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/shipments")


@router.get("/store_shipments_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "store_shipments_routes", "prefix": "/api/v1/shipments"}
