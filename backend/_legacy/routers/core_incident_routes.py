"""core incident routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/incident")


@router.get("/core_incident_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "core_incident_routes", "prefix": "/api/v1/incident"}
