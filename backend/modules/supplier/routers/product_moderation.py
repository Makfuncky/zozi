"""product moderation router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/product-moderation")


@router.get("/product_moderation/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "product_moderation", "prefix": "/api/v1/product-moderation"}
