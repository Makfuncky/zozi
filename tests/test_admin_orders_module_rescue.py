"""Admin orders module rescue tests.

``routers.admin_orders_governance`` previously performed a raw DB write (``db.commit()``)
inline in the ``bulk_update_order_status`` handler (W1 violation). That write
now lives in ``services.orders.bulk_order_service`` and is reached through a
thin controller pass-through, so the router is a read-only orchestration
surface.

This file verifies the runtime wiring (app boots, routes are registered,
auth-gating works) and the architectural constraints (router performs no DB
write; controller delegates the write to the service), plus the service
orchestration logic itself.

NOTE: the shared ``client``/``app`` pytest fixtures in conftest.py are broken
repo-wide. Those are environment issues outside this module, so the
behavioural coverage here uses the app import for wiring only, and pure unit
tests (with a fake DB session) for the service logic.
"""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

from pathlib import Path


BACKEND = Path(__file__).resolve().parent.parent / "backend"


# ── Architecture / wiring (no ORM session needed) ─────────────────────────────

def test_router_has_no_direct_db_write():
    src = BACKEND / "routers" / "admin_orders.py"
    text = src.read_text(encoding="utf-8")
    assert "db.commit(" not in text
    assert "db.add(" not in text
    assert "db.delete(" not in text
    assert "db.refresh(" not in text


def test_controller_delegates_bulk_write_to_service():
    import controllers.admin.orders as ctrl

    assert hasattr(ctrl, "bulk_update_order_status")
    src = (BACKEND / "controllers" / "admin" / "orders.py").read_text(encoding="utf-8")
    # The controller must not define the write inline; it delegates to the service.
    assert "services.orders.bulk_order_service" in src
    assert "_bulk_update_order_status" in src


def test_service_owns_bulk_write():
    import services.orders.bulk_order_service as svc

    assert callable(getattr(svc, "bulk_update_order_status"))


def test_app_boots_and_admin_orders_routes_wired():
    """The app imports and the bulk-status route is registered + auth-gated."""
    import main

    paths = {route.path for route in main.app.routes}
    assert "/api/v1/admin/orders/{country_code}/bulk/status" in paths
    from fastapi.testclient import TestClient

    # An unauthenticated POST to the admin-gated bulk endpoint must return 401,
    # proving the route is mounted and the auth dependency runs (no DB needed).
    with TestClient(main.app) as client:
        resp = client.post(
            "/api/v1/admin/orders/US/bulk/status",
            json={"ids": [1, 2], "status": "shipped"},
        )
    assert resp.status_code == 401


# ── Bulk order service orchestration (pure unit tests, no ORM session) ─────────
# The Order model uses a schema-qualified table (``sales.orders`` or similar)
# which SQLite cannot create in a plain ``sqlite://`` engine. The production
# target is Postgres, so we exercise the service with a fake DB session that
# mirrors the SQLAlchemy query/commit contract.

class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows
        self._filter = None

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        # Return the next matching row (one at a time) to mimic per-id lookups.
        if self._rows:
            return self._rows.pop(0)
        return None


class _FakeOrder:
    def __init__(self, id, status="pending"):
        self.id = id
        self.status = status


class _FakeDB:
    def __init__(self, rows=None):
        self._rows = list(rows or [])
        self.committed = 0

    def query(self, model):
        return _FakeQuery(self._rows)

    def commit(self):
        self.committed += 1


def test_bulk_update_order_status_writes_and_returns_count():
    import services.orders.bulk_order_service as svc

    orders = [_FakeOrder(1, "pending"), _FakeOrder(2, "pending"), _FakeOrder(3, "pending")]
    db = _FakeDB(orders)

    result = svc.bulk_update_order_status([1, 2, 3], "shipped", db)

    assert result == {"message": "Status updated for 3 orders", "updated": 3}
    assert all(o.status == "shipped" for o in orders)
    assert db.committed >= 1


def test_bulk_update_order_status_ignores_missing_orders():
    import services.orders.bulk_order_service as svc

    orders = [_FakeOrder(1, "pending")]
    db = _FakeDB(orders)

    result = svc.bulk_update_order_status([1, 999], "delivered", db)

    assert result == {"message": "Status updated for 1 orders", "updated": 1}
    assert orders[0].status == "delivered"
    assert db.committed >= 1


def test_bulk_update_order_status_empty_ids():
    import services.orders.bulk_order_service as svc

    db = _FakeDB([])
    result = svc.bulk_update_order_status([], "shipped", db)
    assert result == {"message": "Status updated for 0 orders", "updated": 0}
    assert db.committed >= 1
