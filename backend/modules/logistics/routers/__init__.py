"""Routers for the logistics module (re-homed from flat backend/routers/)."""
import importlib

routers = []
public_routers = []

_module_names = [
    "logistics",
    "logistics_health",
    "logistics_health_list",
    "logistics_locations",
    "logistics_locations_create",
    "logistics_logistics_status",
    "logistics_orders_list",
    "logistics_orders_v2",
    "logistics_partner",
    "logistics_partner_verify",
    "parcel_tracking",
    "shipments",
]

for _n in _module_names:
    try:
        _m = importlib.import_module(f"modules.logistics.routers.{_n}")
    except Exception as _e:  # noqa: BLE001
        import logging as _logging
        _logging.getLogger(__name__).error("Skipping router %s: %s", _n, _e)
        continue
    _r = getattr(_m, "router", None)
    if _r is not None:
        routers.append(_r)
    _pr = getattr(_m, "public_router", None)
    if _pr is not None:
        public_routers.append(_pr)
