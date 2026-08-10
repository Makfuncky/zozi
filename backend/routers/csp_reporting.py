"""csp reporting router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/csp-reporting")


@router.get("/csp_reporting/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "csp_reporting", "prefix": "/api/v1/csp-reporting"}
