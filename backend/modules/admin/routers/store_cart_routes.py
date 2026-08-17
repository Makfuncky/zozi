"""store cart routes router.

Business logic lives in `controllers/cart_controller.py`;
wire endpoints here as needed. A `/status` endpoint lists the
controller's public functions for convenience.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/cart")


@router.get("/store_cart_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "store_cart_routes", "prefix": "/api/v1/cart"}


try:
    import controllers.commerce.cart_controller as _ctrl
    _HAS_CTRL = True
    _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]
except Exception:
    _HAS_CTRL = False
    _CTRL_PUBLIC = []


@router.get("/store_cart_routes/status")
def status():
    """Report whether a backing controller is importable."""
    return {"router": "store_cart_routes", "controller": "controllers.commerce.cart_controller" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}
