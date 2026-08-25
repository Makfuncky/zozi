"""Admin chat router — split from comms.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_chat import router as admin_chat_router
    router.include_router(admin_chat_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_chat: %s", _e)

try:
    from .admin_chat_routes import router as admin_chat_routes_router
    router.include_router(admin_chat_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_chat_routes: %s", _e)

try:
    from .chat import router as chat_router
    router.include_router(chat_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip chat: %s", _e)

try:
    from .chat_routes import router as chat_routes_router
    router.include_router(chat_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip chat_routes: %s", _e)

try:
    from .comms_chat import router as comms_chat_router
    router.include_router(comms_chat_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip comms_chat: %s", _e)

