"""Routers for the employee module — 15 domain routers."""
import importlib

routers = []
public_routers = []

_module_names = [
    "accounts",
    "analytics",
    "audit",
    "catalog",
    "comms",
    "country",
    "customers",
    "finance",
    "governance",
    "hr",
    "logistics",
    "orders",
    "promotions",
    "security",
    "suppliers",
]

for _n in _module_names:
    try:
        _m = importlib.import_module(f"modules.employee.routers.{_n}")
    except Exception as _e:
        import logging as _logging
        _logging.getLogger(__name__).error("Skipping router %s: %s", _n, _e)
        continue
    _r = getattr(_m, "router", None)
    if _r is not None:
        routers.append(_r)
    _pr = getattr(_m, "public_router", None)
    if _pr is not None:
        public_routers.append(_pr)
