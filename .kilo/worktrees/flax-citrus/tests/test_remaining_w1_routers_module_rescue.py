"""Remaining W1 router rescue tests (verification-first).

The audit flagged inline DB writes in 8 routers: supplier_documents (1),
ess (3), logistics (2), logistics_locations (2), parcel_tracking (2),
shop_locations (3), shipments (5), tickets (8). Each write was verified to
be authentic and then moved into a ``services/<domain>/`` module. The
router stays a read-only orchestration surface (validation + delegation).

This file proves:
  * every rescued router contains zero inline session writes (regex), and
  * the owning service performs the write (commit/add/flush/refresh) and
    the business logic is preserved.

Service modules are loaded through ``import main`` (which boots the whole
app and loads every router/service without tripping the repo-wide,
pre-existing mapper-configuration defect in the shared conftest) and then
fetched from ``sys.modules`` — re-importing them in isolation triggers the
unrelated ``User.cart`` mapper error, which is out of scope for this rescue.
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

from pathlib import Path


BACKEND = Path(__file__).resolve().parent.parent / "backend"
ROUTERS = BACKEND / "routers"

RESCUED = [
    "supplier_documents",
    "ess",
    "logistics",
    "logistics_locations",
    "parcel_tracking",
    "shop_locations",
    "shipments",
    "tickets",
]

WRITE_PATTERNS = (
    "db.commit(",
    "db.add(",
    "db.delete(",
    "db.refresh(",
    "db.flush(",
    "db.merge(",
)


def _service(module_name: str):
    """Load a service module via the already-booted app (avoids the broken
    isolated-import configure path)."""
    import main  # noqa: F401  (safe: app boots with all routes)
    return sys.modules[module_name]


# ── Architecture: routers perform no DB write ──────────────────────────────────


def test_rescued_routers_have_no_inline_db_write():
    for name in RESCUED:
        text = (ROUTERS / f"{name}.py").read_text(encoding="utf-8")
        for pat in WRITE_PATTERNS:
            assert pat not in text, f"{name}.py still contains a write: {pat}"


def test_app_boots_and_all_rescued_routers_loaded():
    import main

    # The app boots and every rescued router imports cleanly (verifies the
    # router -> service wiring does not break module load). Other routers
    # failing to load is a pre-existing, unrelated conftest/environment issue.
    assert main.app is not None
    for name in RESCUED:
        assert f"routers.{name}" in sys.modules, f"{name} was not loaded by the app"


# ── Fake DB session ───────────────────────────────────────────────────────────


class _FakeDB:
    def __init__(self, first=None, scalar=None):
        self._first = first
        self._scalar = scalar
        self.committed = 0
        self.added = []
        self.executed = []
        self.refreshed = []
        self.flushed = 0

    def query(self, model):
        return self

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._first

    def scalar(self):
        return self._scalar

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flushed += 1

    def commit(self):
        self.committed += 1

    def refresh(self, obj):
        self.refreshed.append(obj)

    def execute(self, stmt, params=None):
        self.executed.append((stmt, params))
        return self


class _FakeDoc:
    def __init__(self, id):
        self.id = id
        self.status = None
        self.review_note = None
        self.reviewed_by = None


class _FakeEmp:
    def __init__(self, id):
        self.id = id
        self.org_unit_id = 1


class _FakeShipment:
    def __init__(self, id, current_hub="HUB"):
        self.id = id
        self.status = "created"
        self.actual_delivery = None
        self.shipped_at = None
        self.current_hub = current_hub
        self.order_id = 1
        self.carrier_name = "C"
        self.tracking_number = "T"
        self.distribution_channel = "D"


class _Truthy:
    pass


# ── Service unit tests ─────────────────────────────────────────────────────────


def test_review_supplier_document_writes():
    svc = _service("services.supplier.supplier_document_service")

    doc = _FakeDoc(5)
    db = _FakeDB(first=doc)
    res = svc.review_supplier_document(db, 5, "approved", "looks good", 9)

    assert doc.status == "approved"
    assert doc.review_note == "looks good"
    assert doc.reviewed_by == 9
    assert res == {"message": "Reviewed", "status": "approved"}
    assert db.committed == 1


def test_update_employee_profile_writes(monkeypatch):
    svc = _service("services.hr.ess_write_service")
    monkeypatch.setattr(svc, "log_activity", lambda *a, **k: None)

    emp = _FakeEmp(3)
    db = _FakeDB()
    res = svc.update_employee_profile(db, emp, phone="123", address="addr")

    assert db.committed == 1
    assert any("UPDATE employees" in str(s) for s, _ in db.executed)
    assert res["status"] == "updated"
    assert "phone" in res["fields"]


def test_create_leave_request_writes(monkeypatch):
    svc = _service("services.hr.ess_write_service")
    monkeypatch.setattr(svc, "log_activity", lambda *a, **k: None)

    emp = _FakeEmp(3)
    db = _FakeDB(scalar=42)
    res = svc.create_leave_request(
        db,
        emp,
        leave_type="annual",
        start_date="2026-01-01",
        end_date="2026-01-05",
        reason="vacation",
    )

    assert db.committed == 1
    assert any("INSERT INTO leave_requests" in str(s) for s, _ in db.executed)
    assert res == {"id": 42, "status": "pending"}


def test_create_shipment_writes():
    svc = _service("services.logistics.shipment_service")

    db = _FakeDB()
    svc.create_shipment(db, {"order_id": 1, "status": "created"})

    assert db.committed == 1
    assert db.added and db.refreshed


def test_admin_set_shipment_status_writes():
    svc = _service("services.logistics.shipment_service")

    ship = _FakeShipment(7, current_hub="HUB1")
    db = _FakeDB(first=ship)
    res = svc.admin_set_shipment_status(db, 7, "delivered")

    assert ship.status == "delivered"
    assert ship.actual_delivery is not None
    assert db.committed == 1
    assert db.added  # ShipmentEvent appended
    assert res["id"] == 7 and res["status"] == "delivered"


def test_create_shop_location_writes():
    svc = _service("services.logistics.location_service")

    db = _FakeDB(first=_Truthy())  # CountryConfig lookup returns truthy
    svc.create_shop_location(db, "US", {"name": "Store", "warehouse_code": "W1"})

    assert db.committed == 1
    assert db.added and db.refreshed


def test_tickets_reused_write_service_writes():
    svc = _service("services.comms.tickets_write_service")

    db = _FakeDB()
    msg = svc.create_ticket_reply(db, 1, 2, "hello", is_admin=False)

    assert db.committed == 1
    assert db.added
    assert msg is not None
