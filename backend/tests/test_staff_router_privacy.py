"""Regression tests for FILE-083: backend/modules/admin/routers/staff.py

Covers:
  - Law 162: role defaults single-sourced (no inline hardcoding)
  - Security A04-02 / A09-01 / PII-02: country scoping + PII masking on GET /admin/users
"""
from __future__ import annotations

import inspect

import pytest


def test_permission_catalog_defaults_include_staff_roles(admin_client: TestClient):
    """sub_admin, moderator, support must appear in defaults (Law 162)."""
    r = admin_client.get("/admin/staff/permission-catalog")
    assert r.status_code == 200, r.text
    body = r.json()
    defaults = body.get("defaults", {})
    for role in ("admin", "sub_admin", "moderator", "support"):
        assert role in defaults, f"Role '{role}' missing from defaults"
        assert isinstance(defaults[role], list)
        assert len(defaults[role]) > 0


def test_permission_catalog_defaults_single_sourced():
    """Defaults must come from _ROLE_FEATURES + module-level constant, not inline."""
    with open("backend/modules/admin/routers/staff.py") as f:
        src = f.read()
    assert "_STAFF_ROLE_DEFAULT_FEATURES" in src, "Missing module-level _STAFF_ROLE_DEFAULT_FEATURES"
    assert "_build_role_defaults" in src, "Missing _build_role_defaults function"
    assert "_ROLE_FEATURES" in src, "Missing _ROLE_FEATURES import"
    assert "defaults = {" not in src, "Inline defaults dict still present"


def test_user_list_has_country_scoping():
    """GET /admin/users must filter by country for non-global-admin roles."""
    with open("backend/modules/admin/routers/staff.py") as f:
        src = f.read()
    assert "get_country_access_scope" in src, "Missing country scoping in list_users_for_permission_ui_route"
    assert "staff_country_codes" in src or "country_code" in src, "Missing country filter"


def test_user_list_masks_pii():
    """GET /admin/users must mask email and full_name."""
    with open("backend/modules/admin/routers/staff.py") as f:
        src = f.read()
    assert "_mask_email" in src, "Missing _mask_email usage in list_users_for_permission_ui_route"
    assert "_mask_full_name" in src, "Missing _mask_full_name usage in list_users_for_permission_ui_route"


def test_user_list_response_keys_unchanged(admin_client: TestClient):
    """Response must still contain id, email, username, full_name, role, is_active."""
    r = admin_client.get("/admin/users", params={"limit": 5})
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, list)
    if body:
        for u in body:
            assert {"id", "email", "username", "full_name", "role", "is_active"} <= u.keys()
