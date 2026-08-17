"""public treasury api access router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("/public_treasury_api_access/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "public_treasury_api_access", "prefix": ""}
