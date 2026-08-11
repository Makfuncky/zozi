"""core video routes router.

Business logic lives in `controllers/video_controller.py`;
wire endpoints here as needed. A `/status` endpoint lists the
controller's public functions for convenience.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/video")


@router.get("/core_video_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "core_video_routes", "prefix": "/api/v1/video"}


try:
    import routers.comms_video as _ctrl
    _HAS_CTRL = True
    _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]
except Exception:
    _HAS_CTRL = False
    _CTRL_PUBLIC = []


@router.get("/core_video_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "core_video_routes", "controller": "routers.comms_video" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}
