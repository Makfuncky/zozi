"""Admin tracking router — split from logistics.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_logistics_operations import router as admin_logistics_operations_router
    router.include_router(admin_logistics_operations_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_logistics_operations: %s", _e)

try:
    from .logistics_operations import router as logistics_operations_router
    router.include_router(logistics_operations_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip logistics_operations: %s", _e)

