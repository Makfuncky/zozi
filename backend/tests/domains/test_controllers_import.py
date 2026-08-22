"""Regression test: the four delegated controllers and their dependent routers
must import cleanly.

These modules previously failed to import (missing controllers, wrong import
paths for providers/services). This test locks that in so a future refactor
cannot silently break the controller -> service boundary again.
"""
import importlib

MODULES = [
    # controllers (the modules created to satisfy the routers)
    "controllers.search.search_controller",
    "controllers.orders.orders_controller",
    "controllers.hr.hr_controller",
    "controllers.unknown.payments_controller",
    # dependent routers
    "routers.search",
    "routers.orders",
    "routers.payments",
    # hr router was migrated to the controller/service architecture: the
    # hand-written routers/hr.py was deleted and replaced by the controller
    # plus its generated surface router.
    "controllers.core.hr_controller",
    "routers.public_core_hr",
    # export controller: the 8 admin export functions (users/orders/products/coupons/
    # audit-logs/transfer/queue/download) must live here as thin wrappers over
    # services.core.export_service. routers/admin.py (the hand-written router that
    # previously imported them) was deleted during the router-consolidation
    # migration, so the regression guard now checks the controller surface directly.
    "controllers.core.export_controller",
    "routers.admin_logistics_operations",
    "routers.public_core_export",
    "services.admin.admin_logistics_operations_service",
]

# Functions routers/admin.py imports from modules.core.routers.export_controller.
# Missing any of these raised ModuleNotFoundError at router-import time and
# triggered the production RuntimeError guard in main._load_routers().
EXPORT_CONTROLLER_FUNCS = [
    "export_users_csv",
    "export_orders_csv",
    "export_products_csv",
    "export_coupons_csv",
    "export_audit_logs_csv",
    "export_transfer_csv",
    "queue_export_job",
    "download_export_job_result",
    "export_pay_equity",
]


def test_controllers_and_dependent_routers_import():
    failures = {}
    for mod in MODULES:
        try:
            importlib.import_module(mod)
        except Exception as exc:  # noqa: BLE001
            failures[mod] = f"{type(exc).__name__}: {exc}"
    assert not failures, "The following modules failed to import:\n" + "\n".join(
        f"  - {m}: {e}" for m, e in failures.items()
    )


def test_export_controller_exposes_admin_export_functions():
    import modules.core.routers.export_controller as ec

    missing = [fn for fn in EXPORT_CONTROLLER_FUNCS if not hasattr(ec, fn)]
    assert not missing, f"export_controller is missing functions imported by routers/admin.py: {missing}"
