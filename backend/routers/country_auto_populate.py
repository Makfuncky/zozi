"""country auto populate router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/country-auto-populate")


@router.get("/country_auto_populate/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "country_auto_populate", "prefix": "/api/v1/country-auto-populate"}
