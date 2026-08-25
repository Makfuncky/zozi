"""Admin disputes router — split from orders.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_disputes_router import router as admin_disputes_router_router
    router.include_router(admin_disputes_router_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_disputes_router: %s", _e)

