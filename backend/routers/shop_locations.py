"""shop locations router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/shop-locations")


@router.get("/shop_locations/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "shop_locations", "prefix": "/api/v1/shop-locations"}
