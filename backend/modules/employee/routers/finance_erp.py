"""finance erp router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/accounting")


@router.get("/finance_erp/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "finance_erp", "prefix": "/api/v1/accounting"}
