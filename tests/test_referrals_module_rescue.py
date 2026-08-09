"""Referrals module rescue tests.

The referrals endpoints were rescued from a router that performed raw DB
reads/writes (W1/Q1) into a thin router -> controller -> service
(``services.referrals_service``) layering. This file verifies both the runtime
wiring (app boots, endpoints are wired, auth works) and the architectural
constraints (router performs no DB access; controller imports no models and no
sibling controllers; endpoints carry response_model) plus the referrals service
orchestration logic itself.

NOTE: the shared ``client``/``app`` pytest fixtures in conftest.py are broken
repo-wide (they depend on a non-existent ``services.core.admin_operations_service``
seed module). Those are environment issues outside the referrals module, so the
behavioural coverage here uses the app import for wiring only, and pure unit
tests (with an isolated in-memory SQLite engine) for the service logic.
"""
from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# ── Architecture / wiring (no ORM session needed) ─────────────────────────────

def test_router_has_no_direct_db_access():
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "backend" / "routers" / "referrals.py"
    text = src.read_text(encoding="utf-8")
    assert "db.query(" not in text
    assert "db.add(" not in text
    assert "db.commit(" not in text
    assert "db.delete(" not in text
    assert "db.refresh(" not in text
    assert "from data.models import Referral" not in text
    assert "from controllers.promotion_controller import" not in text


def test_router_endpoints_have_response_model():
    import routers.public_referrals_management as referrals_router

    for path in ("/config", "/my-code"):
        route = next(r for r in referrals_router.router.routes if getattr(r, "path", None) == path)
        assert route.response_model is not None, f"{path} missing response_model"


def test_controller_does_not_import_models_or_promotion_controller():
    from pathlib import Path

    src = Path(__file__).resolve().parent.parent / "backend" / "controllers" / "referrals_controller.py"
    text = src.read_text(encoding="utf-8")
    assert "from data.models import" not in text
    assert "db.query(" not in text
    assert "from controllers.promotion_controller import" not in text


def test_service_owns_data_access():
    import services.referrals_service as svc

    for name in ("get_referral_config", "get_or_create_referral_code"):
        assert callable(getattr(svc, name))


def test_app_boots_and_referral_endpoint_wired():
    """The app imports and the referral endpoints are registered + auth-gated."""
    import main

    paths = {route.path for route in main.app.routes}
    assert "/api/v1/referrals/config" in paths
    assert "/api/v1/referrals/my-code" in paths
    from fastapi.testclient import TestClient

    # No DB session needed: an unauthenticated GET to the auth-gated endpoint
    # must return 401, proving the route is mounted and the auth dependency runs.
    with TestClient(main.app) as client:
        resp = client.get("/api/v1/referrals/my-code")
    assert resp.status_code == 401


# ── Referrals service orchestration (pure unit tests, no ORM session) ────────
# NOTE: The models use schema-qualified tables (``security.users``,
# ``customer.referrals``) which SQLite cannot create in a plain ``sqlite://``
# engine ("unknown database"). The production target is Postgres where schemas
# exist, so the behavioural coverage here uses a fake DB session that mirrors
# the SQLAlchemy query/commit contract — the same approach as the cart tests.

class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self._result


class _FakeReferral:
    """Lightweight stand-in for the ``Referral`` ORM model.

    Instantiating the real ``Referral`` triggers SQLAlchemy mapper configuration
    for the whole registry, which currently fails on a pre-existing broken
    ``User.cart`` relationship (independent of this module). The service only
    reads/writes ``referrer_id``/``referral_code``/``status``, so a plain object
    is sufficient to exercise the orchestration logic in isolation.
    """

    def __init__(self, referrer_id=None, referral_code=None, status="pending"):
        self.referrer_id = referrer_id
        self.referral_code = referral_code
        self.status = status


# Class-level descriptors so filter expressions like ``Referral.referrer_id == x``
# evaluate without raising (the fake query ignores them).
_FakeReferral.referrer_id = None
_FakeReferral.referral_code = None


class _FakeDB:
    def __init__(self, referral=None, config=None):
        self._referral = referral
        self._config = config
        self.added = None
        self.committed = 0

    def query(self, model):
        # Duck-type: the Referral model (real or monkeypatched fake) exposes referrer_id.
        if hasattr(model, "referrer_id") or getattr(model, "__name__", "") == "Referral":
            return _FakeQuery(self._referral)
        if getattr(model, "__name__", "") == "PromotionEngineConfig":
            return _FakeQuery(self._config)
        return _FakeQuery(None)

    def add(self, obj):
        self.added = obj
        if hasattr(obj, "referrer_id"):
            self._referral = obj

    def commit(self):
        self.committed += 1

    def refresh(self, obj):
        pass


def test_get_referral_config_defaults_when_no_row():
    import services.referrals_service as svc

    cfg = svc.get_referral_config(_FakeDB(config=None))
    assert isinstance(cfg, dict)
    assert cfg["enabled"] is False
    assert cfg["referrer_points"] == 0
    assert cfg["referee_points"] == 0
    assert cfg["monthly_cap"] == 0
    assert cfg["verification_delay_days"] == 0


def test_get_or_create_referral_code_creates_and_is_idempotent(monkeypatch):
    import services.referrals_service as svc

    monkeypatch.setattr(svc, "Referral", _FakeReferral)
    db = _FakeDB(referral=None)
    first = svc.get_or_create_referral_code(1, db)
    assert first["referral_code"]
    assert len(first["referral_code"]) > 0
    assert first["status"] == "pending"
    assert first["referral_url"] == f"/signup?ref={first['referral_code']}"
    assert db.committed >= 1
    assert isinstance(db.added, _FakeReferral)

    # Second call must return the same (existing) code, not create a new one.
    second = svc.get_or_create_referral_code(1, db)
    assert second["referral_code"] == first["referral_code"]


