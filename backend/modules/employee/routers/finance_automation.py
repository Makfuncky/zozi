"""finance automation router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/accounting")


@router.get("/finance_automation/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "finance_automation", "prefix": "/api/v1/accounting"}
