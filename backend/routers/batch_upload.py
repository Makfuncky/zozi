"""batch upload router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/supplier")


@router.get("/batch_upload/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "batch_upload", "prefix": "/api/v1/supplier"}
