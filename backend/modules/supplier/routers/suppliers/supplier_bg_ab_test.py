# === From supplier_bg_ab_test.py ===
from suppliers.router import router  # noqa: F401
"""supplier bg ab test router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/supplier_bg_ab_test/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "supplier_bg_ab_test", "prefix": "/api/v1/supplier"}

