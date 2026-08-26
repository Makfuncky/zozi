# === From hr_dashboard.py ===
from hr.router import router  # noqa: F401
"""hr dashboard router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/hr_dashboard/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "hr_dashboard", "prefix": "/api/v1"}

