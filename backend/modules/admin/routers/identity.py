"""Admin identity router — split from accounts.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_identity_operations import router as admin_identity_operations_router
    router.include_router(admin_identity_operations_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_identity_operations: %s", _e)

try:
    from .identity import router as identity_router
    router.include_router(identity_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip identity: %s", _e)

try:
    from .admin_identity_operations_api import router as admin_identity_operations_api_router
    router.include_router(admin_identity_operations_api_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_identity_operations_api: %s", _e)

try:
    from .identity_api import router as identity_api_router
    router.include_router(identity_api_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip identity_api: %s", _e)

