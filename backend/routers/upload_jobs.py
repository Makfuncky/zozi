"""upload jobs router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("/upload_jobs/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "upload_jobs", "prefix": "/api/v1"}
