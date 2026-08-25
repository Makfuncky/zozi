"""Admin documents router — split from suppliers.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_suppliers_router import router as admin_suppliers_router_router
    router.include_router(admin_suppliers_router_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_suppliers_router: %s", _e)

try:
    from .admin_supplier_reviews import router as admin_supplier_reviews_router
    router.include_router(admin_supplier_reviews_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_supplier_reviews: %s", _e)

