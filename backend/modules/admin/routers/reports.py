"""Admin reports router — split from analytics.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_analytics_fallback_dashboard import router as admin_analytics_fallback_dashboard_router
    router.include_router(admin_analytics_fallback_dashboard_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_analytics_fallback_dashboard: %s", _e)

