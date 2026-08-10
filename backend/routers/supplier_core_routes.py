"""supplier core routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/supplier")


@router.get("/supplier_core_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "supplier_core_routes", "prefix": "/api/v1/supplier"}
