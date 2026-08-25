"""Admin hr router — imports from split sub-modules."""
from fastapi import APIRouter

from .employees import router as employees_router
from .payroll import router as payroll_router
from .hierarchy import router as hierarchy_router

router = APIRouter()

try:
    router.include_router(employees_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip employees_router: %s", _e)

try:
    router.include_router(payroll_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip payroll_router: %s", _e)

try:
    router.include_router(hierarchy_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip hierarchy_router: %s", _e)

