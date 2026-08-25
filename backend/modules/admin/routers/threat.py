"""Admin threat router — split from security.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_security_operations import router as admin_security_operations_router
    router.include_router(admin_security_operations_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_security_operations: %s", _e)

try:
    from .operations import router as operations_router
    router.include_router(operations_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip operations: %s", _e)

