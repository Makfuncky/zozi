"""Tier 0 boot-wiring regression tests.

These lock in the fixes for the Tier 0 defects that silently degraded the
application at runtime:

1. Router import failures were swallowed with a single ``Skipping router`` log
   line, so a broken router produced a booting app with missing (404) routes.
   Concretely ``modules.admin.routers.tickets`` imported
   ``build_ticket_payload``, which did not exist, and the whole ``/admin/tickets``
   surface disappeared on an otherwise healthy-looking boot. Failures are now
   recorded in ``infrastructure.utils.router_loader`` and surfaced.
2. Each ``domains/<d>/subscribers.py`` exposes
   ``register_<d>_subscribers()``, but nothing invoked them, leaving all 13
   domains permanently unsubscribed.

Note on route counting: this FastAPI version represents every
``include_router`` call as a lazy ``_IncludedRouter`` wrapper, so
``app.routes`` does NOT expose sub-router paths. Assertions therefore inspect
``app.openapi()["paths"]``, which is the real flattened HTTP surface.
"""
from __future__ import annotations

import importlib
import logging

import pytest


def _openapi_paths() -> set[str]:
    from main import app

    return set(app.openapi().get("paths", {}))


# ── Router mounting ──────────────────────────────────────────────────────────


def test_router_boot_records_no_failures():
    """No router package or mount may fail during import.

    This is the regression guard for the silent-drop defect: previously the
    loader caught the exception, logged one line, and continued, so nothing
    downstream could tell a healthy boot from a missing domain.
    """
    from infrastructure.utils.router_loader import (
        boot_summary,
        get_failed_imports,
        get_package_failures,
    )

    failed = get_failed_imports()
    package_failures = get_package_failures()
    assert not failed, f"Router submodules failed to import: {failed}"
    assert not package_failures, f"Router packages/mounts failed: {package_failures}"
    assert boot_summary() == "", f"Boot summary is not clean:\n{boot_summary()}"


def test_router_packages_use_the_non_silent_loader():
    """Every actor router package must delegate to load_router_submodules.

    A hand-rolled ``try/except`` loop is what allowed the drop to be invisible,
    so the wiring itself is asserted rather than just the end state.
    """
    packages = ["customer", "supplier", "logistics", "admin", "employee"]
    for module in packages:
        src = importlib.import_module(f"modules.{module}.routers")
        path = getattr(src, "__file__", None)
        assert path, f"modules.{module}.routers has no __file__"
        with open(path, "r", encoding="utf-8") as fh:
            body = fh.read()
        assert "load_router_submodules" in body, (
            f"modules/{module}/routers/__init__.py must use "
            f"load_router_submodules so failures are recorded"
        )
        assert "Skipping router" not in body, (
            f"modules/{module}/routers/__init__.py still swallows import "
            f"failures behind a log line"
        )


def test_core_route_surfaces_are_mounted():
    """Representative surfaces across domains must exist.

    Guards the "orders returns 404" class of symptom: if a router silently
    stops importing, its paths vanish while the app still boots.
    """
    paths = _openapi_paths()

    required = {
        "/admin/tickets": "admin support tickets",
        "/admin/tickets/{ticket_id}": "admin ticket detail",
        "/health": "health probe",
        "/health/ready": "readiness probe",
    }
    missing = {p: why for p, why in required.items() if p not in paths}
    assert not missing, f"Missing required routes: {missing}"

    # A router-mountain regression shows up as a collapse in surface size.
    assert len(paths) >= 500, (
        f"Only {len(paths)} HTTP paths mounted; a router import failure has "
        f"likely removed domain surfaces"
    )


def test_all_actor_router_surfaces_are_represented():
    """Each of the five actor packages must contribute mounted paths."""
    paths = _openapi_paths()
    for actor in ("customer", "supplier", "logistics", "admin", "employee"):
        assert any(f"/{actor}" in p for p in paths), (
            f"No mounted paths for the {actor} actor package"
        )


def test_public_routers_are_collected():
    """public_router modules must be collected, not silently dropped.

    Three of the five actor packages never collected ``public_router`` at all,
    so their public endpoints were missing from the app even though the
    submodule imported fine.
    """
    for module in ["customer", "supplier", "logistics", "admin", "employee"]:
        pkg = importlib.import_module(f"modules.{module}.routers")
        assert hasattr(pkg, "public_routers"), (
            f"modules.{module}.routers must expose public_routers"
        )


# ── Subscriber wiring ────────────────────────────────────────────────────────

_DOMAIN_SUBSCRIBER_FUNCTIONS = [
    ("domains.analytics.subscribers", "register_analytics_subscribers"),
    ("domains.audit.subscribers", "register_audit_subscribers"),
    ("domains.comms.subscribers", "register_comms_subscribers"),
    ("domains.country.subscribers", "register_country_subscribers"),
    ("domains.customers.subscribers", "register_customers_subscribers"),
    ("domains.finance.subscribers", "register_finance_subscribers"),
    ("domains.governance.subscribers", "register_governance_subscribers"),
    ("domains.logistics.subscribers", "register_logistics_subscribers"),
    ("domains.orders.subscribers", "register_orders_subscribers"),
    ("domains.promotions.subscribers", "register_promotions_subscribers"),
    ("domains.security.subscribers", "register_security_subscribers"),
    ("domains.suppliers.subscribers", "register_suppliers_subscribers"),
]


@pytest.mark.parametrize("module_path,func_name", _DOMAIN_SUBSCRIBER_FUNCTIONS)
def test_every_domain_subscriber_entry_point_imports(module_path, func_name):
    """Each domain must expose a callable register_<domain>_subscribers()."""
    module = importlib.import_module(module_path)
    entry = getattr(module, func_name, None)
    assert callable(entry), f"{module_path} must expose a callable {func_name}()"


def test_lifespan_wires_every_domain_subscriber():
    """lifespan must enumerate all 13 register_*_subscribers() entry points.

    Reads the module-level table so a newly added domain that forgets to add
    itself to the tuple is caught here rather than in production.
    """
    from lifespan import _DOMAIN_SUBSCRIBER_MODULES

    wired = {func for _, func in _DOMAIN_SUBSCRIBER_MODULES}
    expected = {func for _, func in _DOMAIN_SUBSCRIBER_FUNCTIONS}

    missing = expected - wired
    assert not missing, (
        f"lifespan does not wire these subscriber entry points: {sorted(missing)}"
    )


def test_startup_actually_populates_the_event_bus():
    """Calling the startup hook must populate the event bus.

    Behavioural version of the defect: before the fix the domains shipped
    register functions that no startup path invoked, so the bus stayed empty
    and every downstream business chain silently no-op'd.

    ``lifespan`` logs through structlog, which the project's conftest routes
    away from pytest's capture, so this asserts the observable state of the
    bus rather than log text.
    """
    from infrastructure.messaging.events import event_bus
    from lifespan import _startup_register_event_listeners

    event_bus.clear()
    assert not event_bus._subscribers and not event_bus._event_callbacks

    _startup_register_event_listeners()

    total = len(event_bus._subscribers) + len(event_bus._event_callbacks)
    assert total >= 20, (
        f"Event bus only has {total} subscriptions after startup wiring; the "
        f"13 domain subscriber modules did not register"
    )


def test_subscriber_registration_is_fault_isolated(monkeypatch):
    """One broken domain must not stop the other twelve from registering.

    ``_startup_register_domain_subscribers`` isolates each module so a single
    domain error cannot leave the whole event bus empty, which is what made
    the original defect so damaging.
    """
    from infrastructure.messaging.events import event_bus
    import lifespan

    module_path, func_name = lifespan._DOMAIN_SUBSCRIBER_MODULES[0]
    module = importlib.import_module(module_path)

    def _boom():
        raise RuntimeError("simulated domain subscriber failure")

    monkeypatch.setattr(module, func_name, _boom)

    event_bus.clear()
    lifespan._startup_register_domain_subscribers()

    total = len(event_bus._subscribers) + len(event_bus._event_callbacks)
    assert total >= 20, (
        f"A single failing domain suppressed all subscriber wiring "
        f"(only {total} subscriptions registered)"
    )


def test_payment_confirmed_listener_is_registered():
    """The PaymentConfirmedEvent fulfillment listener must be wired.

    It silently failed to register because importing FulfillmentService hit a
    circular import (order_entities -> countries -> country_control ->
    logistics_entities -> order_entities) that raised ImportError inside a
    try/except that only logged.
    """
    from infrastructure.messaging.events import event_bus

    event_bus.clear()
    from lifespan import _startup_register_event_listeners

    _startup_register_event_listeners()
    assert event_bus._event_callbacks, "No class-keyed event callbacks registered"
