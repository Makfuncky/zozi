"""store payments routes router.

Business logic lives in `controllers/payments_engine.py`;
wire endpoints here as needed. A `/status` endpoint lists the
engine's public functions for convenience.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/payments")


@router.get("/store_payments_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "store_payments_routes", "prefix": "/api/v1/payments"}


try:
    import domains.payments.models as _ctrl
    _HAS_CTRL = True
    _CTRL_PUBLIC = [n for n in dir(_ctrl) if not n.startswith("_") and callable(getattr(_ctrl, n))]
except Exception:
    _HAS_CTRL = False
    _CTRL_PUBLIC = []


@router.get("/store_payments_routes/status")
def status():
    """Report whether a backing engine is importable."""
    return {"router": "store_payments_routes", "controller": "services.gateways.payments" if _HAS_CTRL else None,
            "public_functions": _CTRL_PUBLIC}
