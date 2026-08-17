"""Routers for the supplier module (re-homed from flat backend/routers/)."""
import importlib

routers = []
public_routers = []

_module_names = [
    "commission",
    "onboarding",
    "product_moderation",
    "product_verification",
    "product_videos",
    "products",
    "supplier",
    "supplier_analytics",
    "supplier_analytics_analytics",
    "supplier_bg_ab_test",
    "supplier_core_routes",
    "supplier_documents",
    "supplier_documents_review",
    "supplier_finance",
    "supplier_finance_status",
    "supplier_health",
    "supplier_health_list",
    "supplier_orders",
    "supplier_orders_verify",
    "supplier_payouts",
    "supplier_payouts_pay",
    "supplier_products",
    "supplier_products_upload",
    "supplier_profile",
    "supplier_profile_create",
    "supplier_supplier_supplier_health",
    "supplier_supplier_sync",
    "supplier_supplier_upload",
]

for _n in _module_names:
    try:
        _m = importlib.import_module(f"modules.supplier.routers.{_n}")
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
