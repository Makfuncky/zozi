"""Admin orders router — imports from split sub-modules."""
from fastapi import APIRouter

from .orders import router as orders_router
from .cart import router as cart_router
from .disputes import router as disputes_router
from .returns import router as returns_router

router = APIRouter()

try:
    router.include_router(orders_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip orders_router: %s", _e)

try:
    router.include_router(cart_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip cart_router: %s", _e)

try:
    router.include_router(disputes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip disputes_router: %s", _e)

try:
    router.include_router(returns_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip returns_router: %s", _e)

