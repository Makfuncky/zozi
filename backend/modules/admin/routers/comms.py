"""Admin comms router — imports from split sub-modules."""
from fastapi import APIRouter

from .chat import router as chat_router
from .email import router as email_router
from .notifications import router as notifications_router
from .tickets import router as tickets_router

router = APIRouter()

try:
    router.include_router(chat_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip chat_router: %s", _e)

try:
    router.include_router(email_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip email_router: %s", _e)

try:
    router.include_router(notifications_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip notifications_router: %s", _e)

try:
    router.include_router(tickets_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip tickets_router: %s", _e)

