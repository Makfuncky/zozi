"""Admin audit router — imports from split sub-modules."""
from fastapi import APIRouter

from .audit import router as audit_router
from .compliance import router as compliance_router

router = APIRouter()

try:
    router.include_router(audit_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip audit_router: %s", _e)

try:
    router.include_router(compliance_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip compliance_router: %s", _e)

