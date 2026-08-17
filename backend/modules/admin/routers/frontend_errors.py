"""frontend errors router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("/frontend_errors/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "frontend_errors", "prefix": "/api/v1"}
