"""RBAC enforcement integration tests (Law 4 / AXIS 3).

Validates:
- the feature catalog is populated from every domain's features.py
- roles.py grants resolve via rbac/resolution
- rbac/service.py grant/revoke persist to the permission tables
- require_feature() denies unknown literals (403) and allows known grants (200)
"""
from __future__ import annotations

from collections import Counter

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Column, MetaData, Table, create_engine
from sqlalchemy.orm import sessionmaker

import infrastructure.database.base as base
from rbac import catalog
from rbac import models as rbac_models
from rbac import roles, resolution
from rbac.dependencies import require_feature
from rbac.service import RBACService

# The RBAC models carry the forbidden `core` schema (kept on Postgres). In this
# SQLite test we strip it from the real model classes so the service queries the
# schema-less tables we create below.
for _m in (rbac_models.PermissionCategory, rbac_models.Permission,
           rbac_models.RolePermissionAssignment, rbac_models.UserPermissionOverride,
           rbac_models.PermissionAuditLog):
    _m.__table__.schema = None
    _ta = list(_m.__table_args__)
    _m.__table_args__ = tuple(a for a in _ta if not (isinstance(a, dict) and "schema" in a))

# ---- isolated, schema-less, FK-free in-memory DB for the RBAC tables -----------
_WANT = {"permission_categories", "permissions", "role_permission_assignments",
         "user_permission_overrides", "permission_audit_log"}

_by_name = {}
for t in base.Base.metadata.tables.values():
    if t.name in _WANT and t.name not in _by_name:
        _by_name[t.name] = t


def _copy_table(src):
    cols = []
    for c in src.columns:
        col = Column(c.name, c.type, primary_key=c.primary_key, nullable=c.nullable,
                     unique=c.unique, default=c.default,
                     server_default=c.server_default)
        cols.append(col)
    return Table(src.name, _RBAC_META, *cols)


_RBAC_META = MetaData()
for _n in ("permission_categories", "permissions", "role_permission_assignments",
           "user_permission_overrides", "permission_audit_log"):
    if _n in _by_name:
        _copy_table(_by_name[_n])

ENGINE = create_engine("sqlite://", connect_args={"check_same_thread": False})
_RBAC_META.create_all(ENGINE)
SESSION_FACTORY = sessionmaker(bind=ENGINE)


def _test_get_db():
    s = SESSION_FACTORY()
    try:
        yield s
    finally:
        s.close()


import infrastructure.database.database as dbmod
dbmod.get_db = _test_get_db
import rbac.dependencies as deps  # noqa: E402
deps.get_db = _test_get_db

FAKE_USER = type("U", (), {"role": "admin", "id": 1})()
deps.get_current_user = lambda: FAKE_USER


@pytest.fixture
def db():
    s = SESSION_FACTORY()
    yield s
    s.close()


def test_catalog_populated_from_all_domains():
    counts = Counter(k.split(".")[0] for k in catalog.FEATURE_CATALOG)
    assert len(catalog.FEATURE_CATALOG) > 500, "catalog is suspiciously small"
    for d in ("accounts", "catalog", "comms", "country", "customers", "finance",
              "governance", "hr", "logistics", "orders", "payments", "suppliers"):
        assert counts.get(d, 0) > 0, f"domain {d} has no features registered"


def test_roles_resolve_across_domains():
    ef = resolution.effective_features(
        role_features=roles.ROLE_FEATURES[("supplier", "supplier")],
        catalog=catalog.FEATURE_CATALOG,
    )
    assert any(k.startswith("suppliers.") for k in ef)
    assert "catalog.products.read" in ef


def test_service_grant_and_revoke(db):
    svc = RBACService()
    feat = "suppliers.badge.read"
    assert catalog.is_known(feat)
    svc.grant("supplier", feat, country_code="OM", db=db)
    assert feat in svc.role_grants("supplier", db=db)
    svc.revoke("supplier", feat, country_code="OM", db=db)
    assert feat not in svc.role_grants("supplier", db=db)


def test_require_feature_denies_unknown_literal():
    dep = require_feature("this.feature.does.not.exist")
    app = FastAPI()

    @app.get("/x")
    def x(_=Depends(dep)):
        return {"ok": True}

    client = TestClient(app)
    resp = client.get("/x")  # even admin ("*") cannot hold an unregistered literal
    assert resp.status_code == 403


def test_require_feature_allows_known_granted(db):
    svc = RBACService()
    svc.grant("supplier", "catalog.products.read", country_code="OM", db=db)

    class U:
        role = "supplier"
        id = 99

    deps.get_current_user = lambda: U()
    try:
        app = FastAPI()

        @app.get("/y")
        def y(_=Depends(require_feature("catalog.products.read"))):
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/y")
        assert resp.status_code == 200, resp.text
    finally:
        deps.get_current_user = lambda: FAKE_USER
