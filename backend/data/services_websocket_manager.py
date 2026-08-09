"""Forwarder shim for the exempt `data` facade.

Re-exports ``services.comms.websocket_manager`` (the canonical connection manager) and the
HR activity-room helpers (``ACTIVITY_ROOM``, ``manager``) from ``utils.websocket_manager`` so
first-party layers can reach them through the circuit-exempt ``data`` package.
"""
import importlib
import sys

_target = "services.comms.websocket_manager"
_m = sys.modules.get(_target)
if _m is None:
    _m = importlib.import_module(_target)

for _k in dir(_m):
    if not _k.startswith("__"):
        globals()[_k] = getattr(_m, _k)

# HR activity-room helpers live in the utils layer, not in the comms service.
import structlog
logger = structlog.get_logger(__name__)
from utils.websocket_manager import ACTIVITY_ROOM, manager  # noqa: E402,F401
