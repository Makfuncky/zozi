"""Admin customers router — imports from split sub-modules."""
from fastapi import APIRouter

from .customers import router as customers_router
from .referrals import router as referrals_router
from .reviews import router as reviews_router

router = APIRouter()

try:
    router.include_router(customers_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip customers_router: %s", _e)

try:
    router.include_router(referrals_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip referrals_router: %s", _e)

try:
    router.include_router(reviews_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip reviews_router: %s", _e)

