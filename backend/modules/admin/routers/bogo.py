"""Admin bogo router — split from promotions.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_promotions import router as admin_promotions_router
    router.include_router(admin_promotions_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_promotions: %s", _e)

try:
    from .promotions import router as promotions_router
    router.include_router(promotions_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip promotions: %s", _e)

try:
    from .admin_promotions_routes import router as admin_promotions_routes_router
    router.include_router(admin_promotions_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_promotions_routes: %s", _e)

try:
    from .admin_promotions_router import router as admin_promotions_router_router
    router.include_router(admin_promotions_router_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_promotions_router: %s", _e)

try:
    from .admin_flash_sales_router import router as admin_flash_sales_router_router
    router.include_router(admin_flash_sales_router_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_flash_sales_router: %s", _e)

