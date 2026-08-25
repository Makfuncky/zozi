"""Admin sessions router — split from accounts.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .core_users_routes import router as core_users_routes_router
    router.include_router(core_users_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip core_users_routes: %s", _e)

