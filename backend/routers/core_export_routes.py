"""core export routes router.

Business logic lives in `controllers/export_controller.py`;
wire endpoints here as needed. A `/status` endpoint lists the
controller's public functions for convenience.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/admin/export")


@router.get("/core_export_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "core_export_routes", "prefix": "/api/v1/admin/export"}


try:
    import controllers.export_controller as _ctrl
    _HAS_CTRL = True
    _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]
except Exception:
    _HAS_CTRL = False
    _CTRL_PUBLIC = []


@router.get("/core_export_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "core_export_routes", "controller": "controllers.export_controller" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}
