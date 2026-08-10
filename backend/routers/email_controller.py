"""email controller router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/email-gateway")


@router.get("/email_controller/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "email_controller", "prefix": "/api/v1/email-gateway"}
