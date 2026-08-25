"""Admin payroll router — split from hr.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .core_payroll_routes import router as core_payroll_routes_router
    router.include_router(core_payroll_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip core_payroll_routes: %s", _e)

try:
    from .admin_hierarchy_router import router as admin_hierarchy_router_router
    router.include_router(admin_hierarchy_router_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_hierarchy_router: %s", _e)

