"""Admin accounts router — imports from split sub-modules."""
from fastapi import APIRouter

from .accounts import router as accounts_router
from .identity import router as identity_router
from .sessions import router as sessions_router

router = APIRouter()

try:
    router.include_router(accounts_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip accounts_router: %s", _e)

try:
    router.include_router(identity_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip identity_router: %s", _e)

try:
    router.include_router(sessions_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip sessions_router: %s", _e)

