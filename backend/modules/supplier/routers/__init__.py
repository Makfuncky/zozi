"""Routers for the supplier module — 6 domain routers."""
import importlib
import logging

logger = logging.getLogger(__name__)

routers = []
public_routers = []

_module_names = [
    "accounts",
    "analytics",
    "catalog",
    "finance",
    "orders",
    "suppliers",
]

for _n in _module_names:
    try:
        _m = importlib.import_module(f"modules.supplier.routers.{_n}")
    except Exception as _e:
        logger.error("Skipping router %s: %s", _n, _e)
        continue
    _r = getattr(_m, "router", None)
    if _r is not None:
        routers.append(_r)
