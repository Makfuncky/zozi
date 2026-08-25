"""Admin promotions router — imports from split sub-modules."""
from fastapi import APIRouter

from .coupons import router as coupons_router
from .banners import router as banners_router
from .bogo import router as bogo_router

router = APIRouter()

try:
    router.include_router(coupons_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip coupons_router: %s", _e)

try:
    router.include_router(banners_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip banners_router: %s", _e)

try:
    router.include_router(bogo_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip bogo_router: %s", _e)

