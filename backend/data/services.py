"""Auto-generated forwarder shim for the exempt `data` facade.

Re-exports ``services`` so first-party layers can reach it through the
circuit-exempt ``data`` package instead of importing it directly.
"""
import importlib
import sys
import structlog
logger = structlog.get_logger(__name__)

_target = "services"
_m = sys.modules.get(_target)
if _m is None:
    _m = importlib.import_module(_target)

for _k in dir(_m):
    if not _k.startswith("__"):
        globals()[_k] = getattr(_m, _k)


def __getattr__(name: str):
    # Forward submodule access, e.g. ``from services import finance_automation``
    # resolves to the ``services.finance.finance_automation`` submodule.
    try:
        return importlib.import_module(f"services.{name}")
    except ModuleNotFoundError as e:
        logger.warning("optional_dependency_unavailable", error=str(e))
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
