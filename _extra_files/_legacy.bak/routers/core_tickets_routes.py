"""core tickets routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/tickets")


@router.get("/core_tickets_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "core_tickets_routes", "prefix": "/api/v1/tickets"}
