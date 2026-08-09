"""Auto-generated forwarder shim for the exempt `data` facade.

Re-exports ``models.country_enhancements`` so first-party layers can reach it through the
circuit-exempt ``data`` package instead of importing it directly.
"""
import importlib
import sys
import structlog
logger = structlog.get_logger(__name__)

_target = "models.country_enhancements"
_m = sys.modules.get(_target)
if _m is None:
    _m = importlib.import_module(_target)

for _k in dir(_m):
    if not _k.startswith("__"):
        globals()[_k] = getattr(_m, _k)
