"""Admin suppliers router — imports from split sub-modules."""
from fastapi import APIRouter

from .suppliers import router as suppliers_router
from .products import router as products_router
from .documents import router as documents_router

router = APIRouter()

try:
    router.include_router(suppliers_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip suppliers_router: %s", _e)

try:
    router.include_router(products_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip products_router: %s", _e)

try:
    router.include_router(documents_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip documents_router: %s", _e)

