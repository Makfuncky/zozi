"""ai research router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/country-research/ai")


@router.get("/ai_research/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "ai_research", "prefix": "/api/v1/country-research/ai"}
