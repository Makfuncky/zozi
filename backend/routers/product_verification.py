"""product verification router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/product-verifications")


@router.get("/product_verification/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "product_verification", "prefix": "/api/v1/product-verifications"}
