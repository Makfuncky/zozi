"""country staff routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/country-staff")


@router.get("/country_staff_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "country_staff_routes", "prefix": "/api/v1/country-staff"}
