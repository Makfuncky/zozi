"""Admin catalog router — imports from split sub-modules."""

from fastapi import APIRouter

from .products import router as products_router
from .categories import router as categories_router
from .search import router as search_router

router = APIRouter()

try:
    router.include_router(products_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip products_router: %s", _e)

try:
    router.include_router(categories_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip categories_router: %s", _e)

try:
    router.include_router(search_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip search_router: %s", _e)

