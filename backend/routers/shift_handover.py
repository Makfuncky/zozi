"""shift handover router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/shift-handover")


@router.get("/shift_handover/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "shift_handover", "prefix": "/api/v1/shift-handover"}
