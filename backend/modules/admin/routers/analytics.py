"""Admin analytics router — imports from split sub-modules."""
from fastapi import APIRouter

from .analytics import router as analytics_router
from .reports import router as reports_router

router = APIRouter()

try:
    router.include_router(analytics_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip analytics_router: %s", _e)

try:
    router.include_router(reports_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip reports_router: %s", _e)

