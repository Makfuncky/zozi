"""Integration tests for paginated API endpoints.

Verifies that the admin and supplier list endpoints return
consistent paginated response envelopes after our refactoring.
"""
from __future__ import annotations
import pytest

pytestmark = pytest.mark.integration


class TestAdminProductsPagination:
    """Tests for GET /admin/products/{country_code} pagination."""

    def test_list_all_products_returns_paginated_envelope(self, admin_client):
        resp = admin_client.get("/api/v1/admin/products/AE?page=1&size=10")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "size" in body
        assert "pages" in body
        assert body["page"] == 1
        assert body["size"] == 10

    def test_list_all_products_page_2(self, admin_client):
        resp = admin_client.get("/api/v1/admin/products/AE?page=2&size=5")
        assert resp.status_code == 200
        body = resp.json()
        assert body["page"] == 2
        assert body["size"] == 5

    def test_list_all_products_with_moderation_filter(self, admin_client):
        resp = admin_client.get("/api/v1/admin/products/AE?moderation_status=approved")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    def test_list_all_products_no_auth(self, client):
        resp = client.get("/api/v1/admin/products/AE")
        assert resp.status_code == 403 or resp.status_code == 401


class TestAdminUsersPagination:
    """Tests for GET /admin/users/{country_code} pagination."""

    def test_list_users_returns_paginated_envelope(self, admin_client):
        resp = admin_client.get("/api/v1/admin/users/AE?page=1&size=20")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "size" in body
        assert "pages" in body

    def test_list_users_with_search(self, admin_client):
        resp = admin_client.get("/api/v1/admin/users/AE?search=admin")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    def test_list_users_with_role_filter(self, admin_client):
        resp = admin_client.get("/api/v1/admin/users/AE?role=admin")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    def test_list_users_no_auth(self, client):
        resp = client.get("/api/v1/admin/users/AE")
        assert resp.status_code == 403 or resp.status_code == 401


class TestSupplierProductsPagination:
    """Tests for GET /supplier-products pagination."""

    def test_list_my_products_returns_paginated_envelope(self, supplier_client):
        resp = supplier_client.get("/api/v1/supplier-products?page=1&size=20")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "size" in body
        assert "pages" in body

    def test_list_my_products_no_auth(self, client):
        resp = client.get("/api/v1/supplier-products")
        assert resp.status_code == 403 or resp.status_code == 401

    def test_list_my_products_page_size(self, supplier_client):
        resp = supplier_client.get("/api/v1/supplier-products?page=1&size=5")
        assert resp.status_code == 200
        body = resp.json()
        assert body["size"] == 5


class TestHealthEndpointVersion:
    """Tests that /health returns versioning info."""

    def test_health_returns_api_version(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert "api_version" in body
        assert body["api_version"] == "/api/v1"
        assert "active_versions" in body
        assert "v1" in body["active_versions"]

    def test_health_returns_app_version(self, client):
        resp = client.get("/api/v1/health")
        body = resp.json()
        assert "version" in body
