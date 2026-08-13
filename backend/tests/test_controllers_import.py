"""Regression test: the four delegated controllers and their dependent routers
must import cleanly.

These modules previously failed to import (missing controllers, wrong import
paths for providers/services). This test locks that in so a future refactor
cannot silently break the controller -> service boundary again.
"""
import importlib

MODULES = [
    # controllers (the modules created to satisfy the routers)
    "controllers.search_controller",
    "controllers.orders_controller",
    "controllers.hr_controller",
    "controllers.payments_controller",
    # dependent routers
    "routers.search",
    "routers.orders",
    "routers.hr",
    "routers.payments",
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
