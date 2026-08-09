"""Supplier orders module rescue tests.

``routers.supplier_orders`` previously performed a raw DB write
(``order.status = "prepared"; db.commit()``) inline in the
``upload_parcel_proof`` handler (W1 violation, audit line 626). That write now
lives in ``services.supplier.supplier_order_service`` and is reached through a
thin controller pass-through, so the router is a read-only orchestration
surface.

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
    src = BACKEND / "routers" / "supplier_orders.py"
    text = src.read_text(encoding="utf-8")
    assert "db.commit(" not in text
    assert "db.add(" not in text
    assert "db.delete(" not in text
    assert "db.refresh(" not in text


def test_controller_delegates_write_to_service():
    import controllers.supplier.orders as ctrl

    assert hasattr(ctrl, "mark_order_prepared_if_processing")
    src = (BACKEND / "controllers" / "supplier" / "orders.py").read_text(encoding="utf-8")
    assert "services.supplier.supplier_order_service" in src
    assert "mark_order_prepared_if_processing" in src


def test_service_owns_write():
    import services.supplier.supplier_order_service as svc

    assert callable(getattr(svc, "mark_order_prepared_if_processing"))


def test_app_boots_and_supplier_orders_routes_wired():
    """The app imports and the parcel-proof route is registered + auth-gated."""
    import main

    paths = {route.path for route in main.app.routes}
    assert "/api/v1/supplier/orders/{order_id}/parcel-proof" in paths
    from fastapi.testclient import TestClient

    with TestClient(main.app) as client:
        resp = client.post("/api/v1/supplier/orders/1/parcel-proof")
    assert resp.status_code == 401


# ── Supplier order service orchestration (pure unit tests, no ORM session) ────
# The Order model uses a schema-qualified table which SQLite cannot create in a
# plain ``sqlite://`` engine. The production target is Postgres, so we exercise
# the service with a fake DB session that mirrors the SQLAlchemy contract.

class _FakeOrder:
    def __init__(self, status="processing"):
        self.status = status


class _FakeDB:
    def __init__(self):
        self.committed = 0

    def commit(self):
        self.committed += 1


def test_mark_order_prepared_transitions_and_commits():
    import services.supplier.supplier_order_service as svc

    order = _FakeOrder("processing")
    db = _FakeDB()

    changed = svc.mark_order_prepared_if_processing(order, db)

    assert changed is True
    assert order.status == "prepared"
    assert db.committed >= 1


def test_mark_order_prepared_noop_when_not_processing():
    import services.supplier.supplier_order_service as svc

    order = _FakeOrder("delivered")
    db = _FakeDB()

    changed = svc.mark_order_prepared_if_processing(order, db)

    assert changed is False
    assert order.status == "delivered"
    assert db.committed == 0
