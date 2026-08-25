"""Admin shipping router — split from logistics.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_logistics import router as admin_logistics_router
    router.include_router(admin_logistics_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_logistics: %s", _e)

try:
    from .shipping import router as shipping_router
    router.include_router(shipping_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip shipping: %s", _e)

try:
    from .admin_logistics_routes import router as admin_logistics_routes_router
    router.include_router(admin_logistics_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_logistics_routes: %s", _e)

try:
    from .logistics_routes import router as logistics_routes_router
    router.include_router(logistics_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip logistics_routes: %s", _e)

