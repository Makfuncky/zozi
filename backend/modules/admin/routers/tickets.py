"""Admin tickets router — split from comms.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_comms_unified import router as admin_comms_unified_router
    router.include_router(admin_comms_unified_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_comms_unified: %s", _e)

try:
    from .unified import router as unified_router
    router.include_router(unified_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip unified: %s", _e)

try:
    from .comms_unified import router as comms_unified_router
    router.include_router(comms_unified_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip comms_unified: %s", _e)

try:
    from .core_video_routes import router as core_video_routes_router
    router.include_router(core_video_routes_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip core_video_routes: %s", _e)

