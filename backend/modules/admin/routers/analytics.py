"""Admin analytics router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .reports import router as reports_router
import logging as _l; _l.getLogger(__name__).warning("skip analytics_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip reports_router: %s", _e)

router = APIRouter(prefix="/api/v1/admin/analytics", tags=["admin", "analytics"])

@router.get("/admin_analytics_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_analytics_routes", "prefix": "/api/v1/admin"}


