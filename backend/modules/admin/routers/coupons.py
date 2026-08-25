"""Admin coupons router — split from promotions.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_coupons_router import router as admin_coupons_router_router
    router.include_router(admin_coupons_router_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_coupons_router: %s", _e)

try:
    from .admin_admin_coupons import router as admin_admin_coupons_router
    router.include_router(admin_admin_coupons_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_admin_coupons: %s", _e)

