"""Admin cart router — split from orders.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_orders_router import router as admin_orders_router_router
    router.include_router(admin_orders_router_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_orders_router: %s", _e)

