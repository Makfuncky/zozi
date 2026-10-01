"""Integration smoke tests for the 3 Phase 7E+2 admin stub-page endpoints.

These exercise:
  - /admin/staff
  - /admin/disputes
  - /admin/staff/permission-catalog
  - /permissions/categories
  - /permissions/list
  - /permissions/roles/admin
  - /admin/users (used by permissions UI)
"""
from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_client(admin_client):
    return admin_client


class TestAdminStaffEndpoint:
    def test_list_staff(self, auth_client: TestClient):
        r = auth_client.get("/admin/staff")
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, list)

    def test_list_staff_role_filter(self, auth_client: TestClient):
        r = auth_client.get("/admin/staff", params={"role": "admin"})
        assert r.status_code == 200, r.text
        for item in r.json():
            assert item.get("role") == "admin"

    def test_permission_catalog(self, auth_client: TestClient):
        r = auth_client.get("/admin/staff/permission-catalog")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "groups" in body and "defaults" in body
        assert isinstance(body["groups"], list) and len(body["groups"]) >= 1
        for group in body["groups"]:
            assert {"key", "label", "permissions"} <= group.keys()
        assert {"admin", "sub_admin", "moderator", "support"} <= body["defaults"].keys()

    def test_users_list_for_picker(self, auth_client: TestClient):
        r = auth_client.get("/admin/users", params={"limit": 5})
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, list)
        for u in body:
            assert {"id", "email"} <= u.keys()


class TestAdminDisputesEndpoint:
    def test_list_disputes(self, auth_client: TestClient):
        r = auth_client.get("/admin/disputes")
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, list)


class TestPermissionsEndpoint:
    def test_list_categories(self, auth_client: TestClient):
        r = auth_client.get("/permissions/categories")
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, list)

    def test_list_permissions(self, auth_client: TestClient):
        r = auth_client.get("/permissions/list")
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, list)

    def test_get_role_permissions(self, auth_client: TestClient):
        r = auth_client.get("/permissions/roles/admin")
        assert r.status_code == 200, r.text
        body = r.json()
        assert isinstance(body, dict)
        # The admin role is expected to have at least one permission granted
        # (if seeded) but the dictionary itself is the contract.
