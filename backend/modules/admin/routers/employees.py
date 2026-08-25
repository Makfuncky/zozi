"""Admin employees router — split from hr.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_staff_router import router as admin_staff_router_router
    router.include_router(admin_staff_router_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_staff_router: %s", _e)

try:
    from .country_staff import router as country_staff_router
    router.include_router(country_staff_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip country_staff: %s", _e)

