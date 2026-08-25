"""Admin auth router — split from security.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_security_registration import router as admin_security_registration_router
    router.include_router(admin_security_registration_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_security_registration: %s", _e)

try:
    from .registration import router as registration_router
    router.include_router(registration_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip registration: %s", _e)

try:
    from .admin_security_health import router as admin_security_health_router
    router.include_router(admin_security_health_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_security_health: %s", _e)

try:
    from .health import router as health_router
    router.include_router(health_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip health: %s", _e)

