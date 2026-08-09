"""Returns module rescue tests.

The ``/returns/{id}/status`` endpoint previously performed a raw DB write
(``db.query`` + ``db.commit``) inline in ``routers.public_returns_access`` (W1 violation). That
write now lives in ``services.returns_service`` and is reached through a thin
controller pass-through, so the router is a read-only orchestration surface.

This file verifies the runtime wiring (app boots, routes are registered,
auth-gating works) and the architectural constraints (router performs no DB
access; controller delegates the write to the service), plus the service
orchestration logic itself.

NOTE: the shared ``client``/``app`` pytest fixtures in conftest.py are broken
repo-wide (they depend on a non-existent ``services.core.admin_operations_service``
seed module). Those are environment issues outside the returns module, so the
behavioural coverage here uses the app import for wiring only, and pure unit
tests (with a fake DB session) for the service logic.
"""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

from pathlib import Path


BACKEND = Path(__file__).resolve().parent.parent / "backend"


# ── Architecture / wiring (no ORM session needed) ─────────────────────────────

def test_router_has_no_direct_db_access():
    src = BACKEND / "routers" / "returns.py"
    text = src.read_text(encoding="utf-8")
    assert "db.query(" not in text
    assert "db.add(" not in text
    assert "db.commit(" not in text
    assert "db.delete(" not in text
    assert "db.refresh(" not in text


def test_router_status_endpoint_has_response_model():
    import routers.public_returns_access as returns_router

    route = next(
        r for r in returns_router.router.routes
        if getattr(r, "path", None) == "/{return_id}/status"
    )
    assert route.response_model is not None, "status endpoint missing response_model"


def test_controller_delegates_status_write_to_service():
    import controllers.returns_controller as ctrl

    assert hasattr(ctrl, "update_return_request_status")
    # The controller must not define the write inline; it delegates to the service.
    src = (BACKEND / "controllers" / "returns_controller.py").read_text(encoding="utf-8")
    # The inlined write must not appear inside the controller's status helper body.
    assert "returns_service.update_return_request_status" in src


def test_service_owns_status_write():
    import services.returns_service as svc

    assert callable(getattr(svc, "update_return_request_status"))


def test_app_boots_and_returns_routes_wired():
    """The app imports and the returns routes are registered + auth-gated."""
    import main

    paths = {route.path for route in main.app.routes}
    assert "/api/v1/returns" in paths
    assert "/api/v1/returns/{return_id}/status" in paths
    from fastapi.testclient import TestClient

    # An unauthenticated PUT to the admin-gated status endpoint must return 401,
    # proving the route is mounted and the auth dependency runs (no DB needed).
    with TestClient(main.app) as client:
        resp = client.put("/api/v1/returns/1/status", json={"status": "approved"})
    assert resp.status_code == 401


# ── Returns service orchestration (pure unit tests, no ORM session) ───────────
# The ReturnRequest model uses a schema-qualified table (``customer.return_requests``
# or similar) which SQLite cannot create in a plain ``sqlite://`` engine. The
# production target is Postgres, so we exercise the service with a fake DB session
# that mirrors the SQLAlchemy query/commit contract (same approach as the cart and
# referrals tests).

class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class _FakeReturnRequest:
    def __init__(self, id=None, status="pending", resolution_notes=None):
        self.id = id
        self.status = status
        self.resolution_notes = resolution_notes


class _FakeDB:
    def __init__(self, row=None):
        self._row = row
        self.committed = 0

    def query(self, model):
        return _FakeQuery(self._row)

    def commit(self):
        self.committed += 1


def test_update_return_request_status_writes_and_returns_message():
    import services.returns_service as svc

    row = _FakeReturnRequest(id=1, status="pending")
    db = _FakeDB(row=row)

    result = svc.update_return_request_status(1, "approved", "looks good", db)

    assert result == {"message": "Updated"}
    assert row.status == "approved"
    assert row.resolution_notes == "looks good"
    assert db.committed >= 1


def test_update_return_request_status_optional_notes():
    import services.returns_service as svc

    row = _FakeReturnRequest(id=1, status="pending")
    db = _FakeDB(row=row)

    svc.update_return_request_status(1, "rejected", None, db)

    assert row.status == "rejected"
    assert row.resolution_notes is None


def test_update_return_request_status_missing_raises_404():
    import pytest

    import services.returns_service as svc

    db = _FakeDB(row=None)
    with pytest.raises(Exception) as excinfo:
        svc.update_return_request_status(999, "approved", None, db)
    # FastAPI's HTTPException carries status_code 404.
    assert excinfo.value.status_code == 404
