"""Routers for the logistics module — 1 domain router."""
import importlib

routers = []
public_routers = []

_module_names = [
    "logistics",
    "accounts",
    "analytics",
]

for _n in _module_names:
    try:
        _m = importlib.import_module(f"modules.logistics.routers.{_n}")
    except Exception as _e:
        import logging as _logging
        _logging.getLogger(__name__).error("Skipping router %s: %s", _n, _e)
        continue
    _r = getattr(_m, "router", None)
    if _r is not None:
        routers.append(_r)
