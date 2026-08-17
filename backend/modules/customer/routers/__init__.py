"""Routers for the customer module (re-homed from flat backend/routers/)."""
import importlib

routers = []
public_routers = []

_module_names = [
    "addresses",
    "cart",
    "coupons",
    "customer_coupons_create",
    "customer_coupons_mgmt",
    "customer_health",
    "customer_health_list",
    "customer_orders",
    "orders",
    "payments",
    "referrals",
    "returns",
    "reviews",
    "wishlist",
]

for _n in _module_names:
    try:
        _m = importlib.import_module(f"modules.customer.routers.{_n}")
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
