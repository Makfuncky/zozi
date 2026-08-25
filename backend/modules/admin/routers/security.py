"""Admin security router — imports from split sub-modules."""
from fastapi import APIRouter

from .fraud import router as fraud_router
from .threat import router as threat_router
from .auth import router as auth_router

router = APIRouter()

try:
    router.include_router(fraud_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip fraud_router: %s", _e)

try:
    router.include_router(threat_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip threat_router: %s", _e)

try:
    router.include_router(auth_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip auth_router: %s", _e)

