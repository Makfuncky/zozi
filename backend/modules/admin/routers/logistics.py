"""Admin logistics router — imports from split sub-modules."""
from fastapi import APIRouter

from .shipping import router as shipping_router
from .tracking import router as tracking_router
from .partners import router as partners_router

router = APIRouter()

try:
    router.include_router(shipping_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip shipping_router: %s", _e)

try:
    router.include_router(tracking_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip tracking_router: %s", _e)

try:
    router.include_router(partners_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip partners_router: %s", _e)

