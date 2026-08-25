"""Admin banners router — split from promotions.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_banners import router as admin_banners_router
    router.include_router(admin_banners_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_banners: %s", _e)

try:
    from .banners import router as banners_router
    router.include_router(banners_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip banners: %s", _e)

try:
    from .admin_banners_routes import router as admin_banners_routes_router
    router.include_router(admin_banners_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_banners_routes: %s", _e)

try:
    from .banners_routes import router as banners_routes_router
    router.include_router(banners_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip banners_routes: %s", _e)

