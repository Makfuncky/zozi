"""store currency routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/currency")


@router.get("/store_currency_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "store_currency_routes", "prefix": "/api/v1/currency"}
