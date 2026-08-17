"""cross border router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/cross-border")


@router.get("/cross_border/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "cross_border", "prefix": "/api/v1/cross-border"}
