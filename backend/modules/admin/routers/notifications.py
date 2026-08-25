"""Admin notifications router — split from comms.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_comms_messaging import router as admin_comms_messaging_router
    router.include_router(admin_comms_messaging_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_comms_messaging: %s", _e)

try:
    from .messaging import router as messaging_router
    router.include_router(messaging_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip messaging: %s", _e)

try:
    from .core_messaging_routes import router as core_messaging_routes_router
    router.include_router(core_messaging_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip core_messaging_routes: %s", _e)

