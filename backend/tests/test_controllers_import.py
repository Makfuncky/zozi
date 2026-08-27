"""Regression test: the delegated controllers and their dependent routers
must import cleanly.

These modules previously failed to import (missing controllers, wrong import
paths for providers/services). This test locks that in so a future refactor
cannot silently break the controller -> service boundary again.
"""
import importlib

MODULES = [
    # governance export controller (reconstructed from controllers migration)
    "domains.governance.services.core.export_controller",
    # domain service controllers
    "modules.admin.routers.catalog",
    "domains.orders.services.orders_controller",
    "domains.hr.services.core.hr_service",
    "domains.finance.services.payments.payments",
    # admin routers that import from controllers
    "modules.admin.routers.admin_logistics_operations",
    "modules.admin.routers.public_core_export",
    "modules.admin.routers.public_core_translate",
    "modules.admin.routers.admin_admin_audit",
    "modules.admin.routers.admin_admin_bank_accounts",
    "modules.admin.routers.admin_admin_misc",
    # supplier routers
    "modules.supplier.routers.supplier",
    "modules.supplier.routers.supplier_supplier_supplier_health",
    # customer routers
    "modules.customer.routers.payments",
    # AI controller (reconstructed stub)
    "domains.governance.services.core.ai_controller",
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
    import domains.governance.services.core.export_controller as ec

    missing = [fn for fn in EXPORT_CONTROLLER_FUNCS if not hasattr(ec, fn)]
    assert not missing, f"export_controller is missing functions imported by routers/admin.py: {missing}"
