"""product videos router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/product-videos")


@router.get("/product_videos/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "product_videos", "prefix": "/api/v1/product-videos"}
