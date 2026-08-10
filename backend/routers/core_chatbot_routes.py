"""core chatbot routes router.

Business logic lives in `controllers/chatbot_controller.py`;
wire endpoints here as needed. A `/status` endpoint lists the
controller's public functions for convenience.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/chatbot")


@router.get("/core_chatbot_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "core_chatbot_routes", "prefix": "/api/v1/chatbot"}


try:
    import controllers.chatbot_controller as _ctrl
    _HAS_CTRL = True
    _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]
except Exception:
    _HAS_CTRL = False
    _CTRL_PUBLIC = []


@router.get("/core_chatbot_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "core_chatbot_routes", "controller": "controllers.chatbot_controller" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}
