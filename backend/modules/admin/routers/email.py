"""Admin email router — split from comms.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_email import router as admin_email_router
    router.include_router(admin_email_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_email: %s", _e)

try:
    from .admin_email_routes import router as admin_email_routes_router
    router.include_router(admin_email_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_email_routes: %s", _e)

try:
    from .email import router as email_router
    router.include_router(email_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip email: %s", _e)

try:
    from .email_routes import router as email_routes_router
    router.include_router(email_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip email_routes: %s", _e)

try:
    from .core_email_routes import router as core_email_routes_router
    router.include_router(core_email_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip core_email_routes: %s", _e)

