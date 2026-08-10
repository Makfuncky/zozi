"""payout approval router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/admin/payout-approval")


@router.get("/payout_approval/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "payout_approval", "prefix": "/api/v1/admin/payout-approval"}
