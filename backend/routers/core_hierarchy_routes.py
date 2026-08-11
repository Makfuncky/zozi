"""core hierarchy routes router.

Business logic lives in `controllers/hierarchy_controller.py`;
wire endpoints here as needed. A `/status` endpoint lists the
controller's public functions for convenience.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/hierarchy")


@router.get("/core_hierarchy_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "core_hierarchy_routes", "prefix": "/api/v1/hierarchy"}


try:
    import controllers.hr.hierarchy_controller as _ctrl
    _HAS_CTRL = True
    _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]
except Exception:
    _HAS_CTRL = False
    _CTRL_PUBLIC = []


@router.get("/core_hierarchy_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "core_hierarchy_routes", "controller": "controllers.hr.hierarchy_controller" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}
