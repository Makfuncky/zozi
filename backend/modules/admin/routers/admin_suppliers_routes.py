"""admin suppliers routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/admin")


@router.get("/admin_suppliers_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_suppliers_routes", "prefix": "/api/v1/admin"}
