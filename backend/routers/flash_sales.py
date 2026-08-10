"""flash sales router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/flash-sales")


@router.get("/flash_sales/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "flash_sales", "prefix": "/api/v1/flash-sales"}
