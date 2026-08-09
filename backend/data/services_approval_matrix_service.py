"""Auto-generated forwarder shim for the exempt `data` facade.

Re-exports ``services.approval_matrix_service`` so first-party layers can reach it through the
circuit-exempt ``data`` package instead of importing it directly.
"""
import importlib
import sys
import structlog
logger = structlog.get_logger(__name__)

_target = "services.approval_matrix_service"
_m = sys.modules.get(_target)
if _m is None:
    _m = importlib.import_module(_target)

for _k in dir(_m):
    if not _k.startswith("__"):
        globals()[_k] = getattr(_m, _k)
