# === From shift_handover.py ===
from hr.router import router  # noqa: F401
"""shift handover router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/shift_handover/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "shift_handover", "prefix": "/api/v1/shift-handover"}

