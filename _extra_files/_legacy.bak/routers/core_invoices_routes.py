"""core invoices routes router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/invoices")


@router.get("/core_invoices_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "core_invoices_routes", "prefix": "/api/v1/invoices"}
