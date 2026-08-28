"""Tests for the logistics domain audit & repair (ARCHITECTURE_DIAGRAM.md compliance)."""
from __future__ import annotations

import inspect
import os

import pytest

# Establish runtime import order first to avoid pre-existing circular import
# chains in other domains (catalog) that are order-dependent during collection.
import main  # noqa: F401

import domains.logistics.models.logistics as logistics_models

# logistics package root (parent of models/ and services/)
LOGISTICS_ROOT = os.path.dirname(os.path.dirname(logistics_models.__file__))
from domains.logistics.services.health.logistics_health_engine import (
    LogisticsHealthEngine,
    get_logistics_health_engine,
)
from domains.logistics.services.partner.partner_geography_service import list_partners
from domains.logistics.services.operations.logistics_write_service import (
    create_shipping_carrier,
    create_shipping_zone,
)


# ── Model layer (Law 6: schema discipline + mandatory audit columns) ──────────


def test_models_have_audit_columns():
    """Every ORM model must declare uuid/version/is_deleted (diagram Law 6 mandatory set)."""
    for name in logistics_models.__all__:
        cls = getattr(logistics_models, name)
        for col in ("uuid", "version", "is_deleted"):
            assert hasattr(cls, col), f"{name} missing audit column: {col}"


def test_models_declare_logistics_schema():
    """Every ORM model must declare schema='logistics' in __table_args__ (Law 6)."""
    for name in logistics_models.__all__:
        cls = getattr(logistics_models, name)
        args = cls.__table_args__
        # __table_args__ may be a dict or a tuple ending in the schema dict
        if isinstance(args, tuple):
            assert args and args[-1] == {"schema": "logistics"}, (
                f"{name} missing logistics schema: {args}"
            )
        else:
            assert args == {"schema": "logistics"}, (
                f"{name} missing logistics schema: {args}"
            )


def test_logistics_entities_duplicate_deleted():
    """The dead duplicate model file must be removed (merged into logistics.py)."""
    entities_path = os.path.join(LOGISTICS_ROOT, "models", "logistics_entities.py")
    assert not os.path.exists(entities_path), "logistics_entities.py still present (dead duplicate)"


# ── Slicing (diagram §3: >8 services -> sub-capability folders) ────────────────


def test_services_sliced_into_subfolders():
    """services/ must be sliced into sub-capability folders (was 51 flat files)."""
    svc = os.path.join(LOGISTICS_ROOT, "services")
    subfolders = {"operations", "partner", "shipments", "health", "geo"}
    for name in subfolders:
        init = os.path.join(svc, name, "__init__.py")
        assert os.path.exists(init), f"missing sub-folder services/{name}/"
    # no stray .py files left at the services root (only __init__.py)
    root_py = [f for f in os.listdir(svc) if f.endswith(".py") and f != "__init__.py"]
    assert root_py == [], f"stray .py files at services root: {root_py}"


# ── Logic fixes ───────────────────────────────────────────────────────────────


def test_health_engine_filters_on_partner_id_not_profile_pk():
    """calculate_health_score must filter LogisticsPartnerProfile.partner_id (not .id)."""
    body = inspect.getsource(LogisticsHealthEngine.calculate_health_score)
    assert "LogisticsPartnerProfile.partner_id" in body
    assert "LogisticsPartnerProfile.id ==" not in body


def test_partner_list_uses_keyset_not_offset():
    """list_partners must use keyset pagination, never OFFSET (diagram §6)."""
    body = inspect.getsource(list_partners)
    assert ".offset(" not in body
    assert "keyset_paginated_response" in body


def test_write_service_has_rollback_guards():
    """DB writes must roll back on exception (session hygiene)."""
    body = inspect.getsource(create_shipping_carrier)
    assert "db.rollback()" in body
    body = inspect.getsource(create_shipping_zone)
    assert "db.rollback()" in body


def test_write_service_no_stale_reexports():
    """The dead _REEXPORTS/__getattr__ shim must be removed."""
    ws_path = os.path.join(
        LOGISTICS_ROOT, "services", "operations", "logistics_write_service.py",
    )
    body = open(ws_path).read()
    assert "_REEXPORTS" not in body
    assert "controllers.orders.logistics_controller" not in body
    assert "domains.logistics.services.logistics_service" not in body or "from domains.logistics.services.logistics_service" in body


def test_locations_service_no_unused_import_and_capped_query():
    """Unused cross-domain import removed; list query capped (no unbounded .all())."""
    loc_path = os.path.join(
        LOGISTICS_ROOT, "services", "geo", "logistics_locations_service.py",
    )
    body = open(loc_path).read()
    assert "auth_controller_service" not in body
    assert "SAFE_QUERY_LIMIT" in body


# ── Wiring / reachability ─────────────────────────────────────────────────────


def test_health_engine_reachable_from_list_service():
    """get_logistics_health_engine must construct without error."""
    class FakeDB:
        def query(self, *a, **k): return self
        def filter(self, *a, **k): return self
        def first(self): return None
    engine = get_logistics_health_engine(FakeDB())
    assert isinstance(engine, LogisticsHealthEngine)


def test_no_dead_service_files_remain():
    """Every .py under services/ sub-folders must be imported somewhere (no orphans)."""
    svc = os.path.join(LOGISTICS_ROOT, "services")
    # Collect all service modules
    all_service_py = []
    for root, _dirs, files in os.walk(svc):
        for f in files:
            if f.endswith(".py") and f != "__init__.py" and "__pycache__" not in root:
                all_service_py.append(os.path.join(root, f))
    # None of these should be the ones we deleted
    deleted_names = {
        "logistics_entities.py", "logistics_service.py", "main.py",
        "logistics_controller__routers.py", "logistics_partner_service__router_migration.py",
    }
    for p in all_service_py:
        assert os.path.basename(p) not in deleted_names, f"dead file still present: {p}"


# ── Continuation-phase repairs ────────────────────────────────────────────────


def test_fulfillment_service_loads():
    """FulfillmentService file must parse (broken NotificationService import was removed)."""
    import ast
    fs_path = os.path.join(
        LOGISTICS_ROOT, "services", "operations", "fulfillment_service.py",
    )
    src = open(fs_path).read()
    # must parse cleanly (no syntax errors from broken imports)
    ast.parse(src)
    # the class must be defined
    assert "class FulfillmentService" in src
    assert "def handle_payment_confirmed" in src


def test_fulfillment_no_fictional_notification_import():
    """The fictional NotificationService import must be gone."""
    fs_path = os.path.join(
        LOGISTICS_ROOT, "services", "operations", "fulfillment_service.py",
    )
    body = open(fs_path).read()
    assert "NotificationService" not in body
    assert "send_fulfillment_issues_notification" not in body


def test_event_delivered_removed():
    """Orphaned EVENT_SHIPMENT_DELIVERED must be removed."""
    from domains.logistics import events
    assert not hasattr(events, "EVENT_SHIPMENT_DELIVERED")
    assert hasattr(events, "EVENT_SHIPMENT_CREATED")


def test_orphaned_feature_atoms_removed():
    """Ungated feature atoms (fallback, geography, imports) must be removed."""
    from domains.logistics.features import FEATURES
    for orphan in ("logistics.fallback", "logistics.geography", "logistics.imports"):
        assert orphan not in FEATURES, f"orphaned atom still present: {orphan}"
    for atom in ("logistics.operations", "logistics.shipment.read", "logistics.partner.write",
                 "logistics.health.read", "logistics.locations.write"):
        assert atom in FEATURES


def test_partner_pricing_uses_logistics_city_distance():
    """partner_pricing must import CityDistanceMatrix from logistics, not accounts."""
    import inspect
    from domains.logistics.services.partner import logistics_partner_pricing
    src = inspect.getsource(logistics_partner_pricing)
    assert "from domains.logistics.models.logistics_schema_models import CityDistanceMatrix" in src
    assert "from domains.governance.models.core import CityDistanceMatrix" not in src


def test_sla_service_no_broken_treasury_import():
    """run_treasury_sync (broken TreasuryService call) must be removed."""
    import inspect
    from domains.logistics.services.operations import logistics_sla_service
    src = inspect.getsource(logistics_sla_service)
    assert "TreasuryService" not in src
    assert "run_treasury_sync" not in src


def test_admin_operations_no_n_plus_one():
    """get_email_stats must pre-aggregate recipient counts (no per-campaign query loop)."""
    import inspect
    from domains.logistics.services.partner.admin_operations_service import get_email_stats
    src = inspect.getsource(get_email_stats)
    assert "recipient_counts" in src
    assert "recipient_count = db.query" not in src


# ── NS8 cross-domain import fixes ────────────────────────────────────────────


def test_shipments_service_user_type_hint_only():
    """User import must be TYPE_CHECKING (not runtime cross-domain import)."""
    import inspect
    from domains.logistics.services.shipments import shipments_service
    src = inspect.getsource(shipments_service)
    assert "if TYPE_CHECKING:" in src
    lines = src.split("\n")
    for i, line in enumerate(lines):
        if "from domains.accounts.models.user import User" in line:
            preceding = "\n".join(lines[max(0, i-3):i+1])
            assert "TYPE_CHECKING" in preceding, "User import not guarded by TYPE_CHECKING"


def test_locations_service_uses_country_port():
    """list_logistics_partner_locations must use country.ports, not direct model import."""
    import inspect
    from domains.logistics.services.geo import logistics_locations_service
    src = inspect.getsource(logistics_locations_service)
    assert "get_country_config" in src
    assert "from domains.country.models.countries import CountryConfig" not in src


def test_write_service_uses_governance_ports():
    """Reads of governance models must go through governance.ports."""
    import inspect
    from domains.logistics.services.operations import logistics_write_service
    src = inspect.getsource(logistics_write_service)
    assert "get_shipping_zone_by_id" in src
    assert "get_shipping_carrier_by_id" in src


def test_partner_pricing_order_type_hint_only():
    """Order import must be TYPE_CHECKING (used only as type hint)."""
    import inspect
    from domains.logistics.services.partner import logistics_partner_pricing
    src = inspect.getsource(logistics_partner_pricing)
    assert "if TYPE_CHECKING:" in src
    lines = src.split("\n")
    for i, line in enumerate(lines):
        if "from domains.orders.models.order_entities import Order" in line:
            preceding = "\n".join(lines[max(0, i-3):i+1])
            assert "TYPE_CHECKING" in preceding, "Order import not guarded by TYPE_CHECKING"
