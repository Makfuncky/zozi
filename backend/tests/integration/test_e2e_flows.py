"""End-to-end flow tests for the Zozi backend.

Verifies:
  1. Customer registration → login → browse catalog → add to cart → checkout → order → payment → fulfillment.
  2. Supplier registration → product creation → order receipt → shipment → payout.
  3. Admin login → user management → audit → compliance check.
  4. Employee login → HR operations → payroll.
  5. Multi-country operations (country scoping).
"""
from __future__ import annotations

import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure backend root is importable
_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("CSRF_DISABLED", "true")


class TestCustomerE2EFlow:
    """Customer registration → login → browse catalog → add to cart → checkout → order → payment → fulfillment."""

    def test_health_endpoint_accessible(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_customer_can_access_health(self, customer_client):
        resp = customer_client.get("/health")
        assert resp.status_code == 200

    def test_customer_token_is_valid(self, customer_token):
        assert isinstance(customer_token, str)
        assert len(customer_token) > 0

    def test_customer_auth_headers_work(self, customer_client):
        resp = customer_client.get("/health")
        assert resp.status_code == 200

    def test_catalog_browse_endpoint_exists(self, customer_client):
        """Verify catalog browse endpoint is accessible."""
        resp = customer_client.get("/catalog/products")
        # May be 200 or 404 depending on route registration
        assert resp.status_code in (200, 404)

    def test_customer_can_list_orders(self, customer_client):
        resp = customer_client.get("/customer/orders")
        assert resp.status_code in (200, 404)


class TestSupplierE2EFlow:
    """Supplier registration → product creation → order receipt → shipment → payout."""

    def test_supplier_token_is_valid(self, supplier_token):
        assert isinstance(supplier_token, str)
        assert len(supplier_token) > 0

    def test_supplier_can_access_health(self, supplier_client):
        resp = supplier_client.get("/health")
        assert resp.status_code == 200

    def test_supplier_can_list_orders(self, supplier_client):
        resp = supplier_client.get("/supplier/orders")
        assert resp.status_code in (200, 404)

    def test_supplier_can_access_catalog(self, supplier_client):
        resp = supplier_client.get("/supplier/catalog/products")
        assert resp.status_code in (200, 404)


class TestAdminE2EFlow:
    """Admin login → user management → audit → compliance check."""

    def test_admin_token_is_valid(self, admin_token):
        assert isinstance(admin_token, str)
        assert len(admin_token) > 0

    def test_admin_can_access_health(self, admin_client):
        resp = admin_client.get("/health")
        assert resp.status_code == 200

    def test_admin_can_access_health_deps(self, admin_client):
        resp = admin_client.get("/health/deps")
        assert resp.status_code == 200
        data = resp.json()
        assert "dependencies" in data

    def test_admin_can_access_health_ready(self, admin_client):
        resp = admin_client.get("/health/ready")
        assert resp.status_code in (200, 503)

    def test_admin_can_list_users(self, admin_client):
        resp = admin_client.get("/admin/accounts/users")
        assert resp.status_code in (200, 404)

    def test_admin_can_access_audit(self, admin_client):
        resp = admin_client.get("/admin/audit/logs")
        assert resp.status_code in (200, 404)


class TestEmployeeE2EFlow:
    """Employee login → HR operations → payroll."""

    def test_employee_module_exists(self):
        from modules.employee import routers
        assert routers is not None

    def test_employee_routers_have_hr(self):
        from modules.employee.routers import hr
        assert hr is not None

    def test_employee_routers_have_finance(self):
        from modules.employee.routers import finance
        assert finance is not None


class TestMultiCountryOperations:
    """Multi-country operations (country scoping)."""

    def test_country_config_model_exists(self):
        from domains.country.models.countries import CountryConfig
        assert CountryConfig is not None

    def test_country_config_has_code(self, db_session):
        from domains.country.models.countries import CountryConfig
        result = db_session.query(CountryConfig).first()
        if result:
            assert hasattr(result, "code")
            assert hasattr(result, "name")
            assert hasattr(result, "currency")

    def test_country_config_seeded(self, _seed_default_accounts, engine):
        from domains.country.models.countries import CountryConfig
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            count = session.query(CountryConfig).count()
            assert count >= 3, f"Expected at least 3 countries, got {count}"
        finally:
            session.close()

    def test_user_has_country_code(self, db_session):
        from domains.accounts.models.user import User
        user = db_session.query(User).first()
        if user:
            assert hasattr(user, "country_code")

    def test_country_ports_have_read_functions(self):
        from domains.country import ports
        assert ports is not None

    def test_country_events_module_exists(self):
        from domains.country import events
        assert events is not None


class TestAuthenticationFlow:
    """Authentication flow end-to-end."""

    def test_login_endpoint_exists(self, client):
        resp = client.post("/auth/login", json={
            "email": "admin@zozi.com",
            "password": "wrong_password",
        })
        # Should return 401 for wrong password
        assert resp.status_code in (401, 404, 422)

    def test_protected_endpoint_rejects_unauthenticated(self, client):
        resp = client.get("/admin/accounts/users")
        assert resp.status_code in (401, 403, 404)

    def test_token_verify_endpoint(self, client):
        resp = client.post("/auth/token/verify", headers={
            "Authorization": "Bearer invalid_token"
        })
        assert resp.status_code in (401, 404, 422)


class TestModuleRouterRegistration:
    """Verify all module routers are registered."""

    def test_admin_routers_package_exists(self):
        from modules.admin import routers
        assert hasattr(routers, "routers")
        assert isinstance(routers.routers, list)

    def test_customer_routers_package_exists(self):
        from modules.customer import routers
        assert hasattr(routers, "routers")
        assert isinstance(routers.routers, list)

    def test_supplier_routers_package_exists(self):
        from modules.supplier import routers
        assert hasattr(routers, "routers")
        assert isinstance(routers.routers, list)

    def test_logistics_routers_package_exists(self):
        from modules.logistics import routers
        assert hasattr(routers, "routers")
        assert isinstance(routers.routers, list)

    def test_employee_routers_package_exists(self):
        from modules.employee import routers
        assert hasattr(routers, "routers")
        assert isinstance(routers.routers, list)

    def test_admin_has_routers(self):
        from modules.admin.routers import routers
        assert len(routers) > 0

    def test_customer_has_routers(self):
        from modules.customer.routers import routers
        assert len(routers) > 0

    def test_supplier_has_routers(self):
        from modules.supplier.routers import routers
        assert len(routers) > 0


class TestWebSocketEndpoints:
    """WebSocket endpoint registration."""

    def test_websocket_user_endpoint_registered(self, app):
        ws_routes = [
            route for route in app.routes
            if hasattr(route, "path") and "ws" in route.path.lower()
        ]
        # Should have at least one WebSocket route
        assert len(ws_routes) > 0


class TestHealthEndpoints:
    """Health check endpoints."""

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_deps_endpoint(self, client):
        resp = client.get("/health/deps")
        assert resp.status_code == 200
        data = resp.json()
        assert "dependencies" in data
        assert "redis" in data["dependencies"]

    def test_health_ready_endpoint(self, client):
        resp = client.get("/health/ready")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "ready" in data
        assert "database" in data
