"""Admin products router — split from suppliers.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_products import router as admin_products_router
    router.include_router(admin_products_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_products: %s", _e)

try:
    from .supplier_products import router as supplier_products_router
    router.include_router(supplier_products_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip supplier_products: %s", _e)

try:
    from .supplier_products_routes import router as supplier_products_routes_router
    router.include_router(supplier_products_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip supplier_products_routes: %s", _e)

