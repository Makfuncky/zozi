"""Admin referrals router — split from customers.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .public_commerce_referrals import router as public_commerce_referrals_router
    router.include_router(public_commerce_referrals_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip public_commerce_referrals: %s", _e)

