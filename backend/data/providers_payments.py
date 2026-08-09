"""Auto-generated forwarder shim for the exempt `data` facade.

Re-exports ``providers.payments`` so first-party layers can reach it through the
circuit-exempt ``data`` package instead of importing it directly.
"""
import importlib
import sys
import structlog
logger = structlog.get_logger(__name__)

_target = "providers.payments"
_m = sys.modules.get(_target)
if _m is None:
    _m = importlib.import_module(_target)

__all__ = [k for k in dir(_m) if not k.startswith("_")]
for _k in __all__:
    globals()[_k] = getattr(_m, _k)
