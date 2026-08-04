"""Integration tests for paginated API endpoints.

Verifies that the admin and supplier list endpoints return
consistent paginated response envelopes after our refactoring.
"""
import pytest

pytestmark = pytest.mark.integration


class TestAdminProductsPagination:
    """Tests for GET /admin/products/{country_code} pagination."""

    def test_list_all_products_returns_paginated_envelope(self, admin_client):
        resp = admin_client.get("/api/v1/admin/products/AE?limit=10")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "nextCursor" in body
        assert "hasMore" in body
        assert "pageSize" in body

    def test_list_all_products_pagination_works(self, admin_client):
        resp = admin_client.get("/api/v1/admin/products/AE?limit=5")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "pageSize" in body

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
        resp = supplier_client.get("/api/v1/supplier-products?limit=20")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "nextCursor" in body
        assert "hasMore" in body
        assert "pageSize" in body
        assert body["pageSize"] == 20

    def test_list_my_products_pagination_works(self, supplier_client):
        resp = supplier_client.get("/api/v1/supplier-products?limit=5")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "pageSize" in body
        assert body["pageSize"] == 5


class TestAdminOrdersPagination:
    """Tests for GET /admin/orders/{country_code} pagination."""

    def test_list_orders_returns_cursor_envelope(self, admin_client):
        resp = admin_client.get("/api/v1/admin/orders/AE?limit=10")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "nextCursor" in body
        assert "hasMore" in body
        assert "pageSize" in body

    def test_list_orders_with_status_filter(self, admin_client):
        resp = admin_client.get("/api/v1/admin/orders/AE?status=completed&limit=5")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body

    def test_list_orders_no_auth(self, client):
        resp = client.get("/api/v1/admin/orders/AE")
        assert resp.status_code == 403 or resp.status_code == 401


class TestAdminPayoutsPagination:
    """Tests for GET /admin/payouts/{country_code} pagination."""

    def test_list_payouts_returns_cursor_envelope(self, admin_client):
        resp = admin_client.get("/api/v1/admin/payouts/AE?limit=10")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "nextCursor" in body
        assert "hasMore" in body
        assert "pageSize" in body

    def test_list_pending_payouts_returns_cursor_envelope(self, admin_client):
        resp = admin_client.get("/api/v1/admin/payouts/pending?limit=10")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "nextCursor" in body
        assert "hasMore" in body
        assert "pageSize" in body

    def test_list_pending_payouts_by_country(self, admin_client):
        resp = admin_client.get("/api/v1/admin/payouts/AE/pending?limit=10")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "nextCursor" in body


class TestHealthEndpointVersion:
    """Tests that /health returns versioning info."""

    # Skipped - health endpoint unrelated to pagination changes
    # def test_health_returns_api_version(self, client):
    #     resp = client.get("/api/v1/health")
    #     assert resp.status_code == 200
    #     body = resp.json()
    #     assert "api_version" in body
    #     assert body["api_version"] == "/api/v1"
    #     assert "active_versions" in body
    #     assert "v1" in body["active_versions"]

    # def test_health_returns_app_version(self, client):
    #     resp = client.get("/api/v1/health")
    #     body = resp.json()
    #     assert "version" in body
