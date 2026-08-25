"""Admin reviews router — split from customers.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_supplier_reviews import router as admin_supplier_reviews_router
    router.include_router(admin_supplier_reviews_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_supplier_reviews: %s", _e)

try:
    from .public_commerce_reviews import router as public_commerce_reviews_router
    router.include_router(public_commerce_reviews_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip public_commerce_reviews: %s", _e)

