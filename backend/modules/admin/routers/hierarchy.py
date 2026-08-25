"""Admin hierarchy router — split from hr.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_hierarchy_router import router as admin_hierarchy_router_router
    router.include_router(admin_hierarchy_router_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_hierarchy_router: %s", _e)

try:
    from .core_hierarchy_routes import router as core_hierarchy_routes_router
    router.include_router(core_hierarchy_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip core_hierarchy_routes: %s", _e)

try:
    from .public_hr_hierarchy import router as public_hr_hierarchy_router
    router.include_router(public_hr_hierarchy_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip public_hr_hierarchy: %s", _e)

