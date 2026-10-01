"""HR health-check sub-router — liveness probes."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/shift_handover/health")
def shift_handover_health():
    """Liveness probe for shift handover router."""
    return {"status": "ok", "router": "shift_handover", "prefix": "/api/v1/shift-handover"}


@router.get("/hr_dashboard/health")
def hr_dashboard_health():
    """Liveness probe for HR dashboard router."""
    return {"status": "ok", "router": "hr_dashboard", "prefix": "/api/v1"}