"""store banners routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/banners")


@router.get("/store_banners_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "store_banners_routes", "prefix": "/api/v1/banners"}
