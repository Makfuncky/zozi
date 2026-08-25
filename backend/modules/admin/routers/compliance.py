"""Admin compliance router — split from audit.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_geography_audit import router as admin_geography_audit_router
    router.include_router(admin_geography_audit_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_geography_audit: %s", _e)

try:
    from .geography_audit import router as geography_audit_router
    router.include_router(geography_audit_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip geography_audit: %s", _e)

try:
    from .core_compliance_routes import router as core_compliance_routes_router
    router.include_router(core_compliance_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip core_compliance_routes: %s", _e)

