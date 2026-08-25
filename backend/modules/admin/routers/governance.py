"""Admin governance router — imports from split sub-modules."""

from fastapi import APIRouter

from .admin import router as admin_router
from .permissions import router as permissions_router
from .fraud import router as fraud_router
from .risk import router as risk_router

router = APIRouter()

try:
    router.include_router(admin_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_router: %s", _e)

try:
    router.include_router(permissions_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip permissions_router: %s", _e)

try:
    router.include_router(fraud_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip fraud_router: %s", _e)

try:
    router.include_router(risk_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip risk_router: %s", _e)

