"""Admin fraud router — split from security.py."""
from fastapi import APIRouter
from typing import Optional

router = APIRouter()

try:
    from .admin_security_detection import router as admin_security_detection_router
    router.include_router(admin_security_detection_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip admin_security_detection: %s", _e)

try:
    from .detection import router as detection_router
    router.include_router(detection_router)
except Exception as _e:
    import logging as _l; _l.getLogger(__name__).warning("skip detection: %s", _e)

