"""core ess routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/ess")


@router.get("/core_ess_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "core_ess_routes", "prefix": "/api/v1/ess"}
