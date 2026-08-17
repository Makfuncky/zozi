"""admin settings routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/admin/settings")


@router.get("/admin_settings_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_settings_routes", "prefix": "/api/v1/admin/settings"}
