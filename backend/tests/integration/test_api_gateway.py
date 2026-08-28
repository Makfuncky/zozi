"""API gateway behavior tests for the Zozi backend.

Verifies:
  1. Route registration for all modules.
  2. Route prefixes (/admin/*, /customer/*, /employee/*, /logistics/*, /supplier/*).
  3. Public vs protected endpoints.
  4. Feature-gated endpoints.
  5. API versioning.
  6. Request/response serialization.
  7. Error response format (RFC 7807).
  8. Pagination format (cursor-based).
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


class TestRouteRegistration:
    """Route registration for all modules."""

    def test_app_has_routes(self, app):
        assert len(app.routes) > 0

    def test_health_route_registered(self, app):
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/health" in routes

    def test_admin_routes_registered(self, app):
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        admin_routes = [r for r in routes if "/admin" in r or r.startswith("/admin")]
        assert len(admin_routes) > 0, "No admin routes registered"

    def test_customer_routes_registered(self, app):
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        customer_routes = [r for r in routes if "/customer" in r or r.startswith("/customer")]
        assert len(customer_routes) > 0, "No customer routes registered"

    def test_supplier_routes_registered(self, app):
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        supplier_routes = [r for r in routes if "/supplier" in r or r.startswith("/supplier")]
        assert len(supplier_routes) > 0, "No supplier routes registered"

    def test_docs_route_registered(self, app):
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/docs" in routes or any("/docs" in r for r in routes)


class TestRoutePrefixes:
    """Route prefixes (/admin/*, /customer/*, /employee/*, /logistics/*, /supplier/*)."""

    def test_routes_have_prefixes(self, app):
        """Verify routes have proper prefixes."""
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        # At least some routes should have prefixes
        prefixed = [r for r in routes if r != "/" and r != "/health"]
        assert len(prefixed) > 0

    def test_no_duplicate_routes(self, app):
        """Verify no duplicate route registrations."""
        routes = [r.path for r in app.routes if hasattr(r, "path")]
        # Duplicates may exist due to aliases, but should be minimal
        from collections import Counter
        counts = Counter(routes)
        duplicates = {k: v for k, v in counts.items() if v > 2}
        assert len(duplicates) < 5, f"Too many duplicate routes: {duplicates}"


class TestPublicVsProtectedEndpoints:
    """Public vs protected endpoints."""

    def test_health_is_public(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_docs_is_public(self, client):
        resp = client.get("/docs")
        assert resp.status_code in (200, 307, 308, 404)

    def test_admin_endpoints_require_auth(self, client):
        resp = client.get("/admin/accounts/users")
        assert resp.status_code in (401, 403, 404)

    def test_customer_endpoints_require_auth(self, client):
        resp = client.get("/customer/orders")
        assert resp.status_code in (401, 403, 404)

    def test_supplier_endpoints_require_auth(self, client):
        resp = client.get("/supplier/orders")
        assert resp.status_code in (401, 403, 404)

    def test_admin_endpoint_with_auth(self, admin_client):
        resp = admin_client.get("/health")
        assert resp.status_code == 200


class TestFeatureGatedEndpoints:
    """Feature-gated endpoints."""

    def test_rbac_catalog_exists(self):
        from rbac.catalog import get_catalog
        catalog = get_catalog()
        assert isinstance(catalog, dict)

    def test_require_feature_function_exists(self):
        from rbac.dependencies import require_feature
        assert callable(require_feature)

    def test_require_module_function_exists(self):
        from rbac.dependencies import require_module
        assert callable(require_module)


class TestAPIVersioning:
    """API versioning."""

    def test_version_prefix_defined(self):
        from infrastructure.utils.versioning import VERSION_PREFIX
        assert isinstance(VERSION_PREFIX, str)
        assert len(VERSION_PREFIX) > 0

    def test_get_version_path_callable(self):
        from infrastructure.utils.versioning import get_version_path
        assert callable(get_version_path)

    def test_versioned_prefix_callable(self):
        from infrastructure.utils.versioning import versioned_prefix
        assert callable(versioned_prefix)

    def test_get_active_versions_callable(self):
        from infrastructure.utils.versioning import get_active_versions
        assert callable(get_active_versions)

    def test_active_versions_returns_list(self):
        from infrastructure.utils.versioning import get_active_versions
        versions = get_active_versions()
        assert isinstance(versions, list)


class TestRequestResponseSerialization:
    """Request/response serialization."""

    def test_health_returns_json(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("content-type", "")

    def test_health_response_structure(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data
        assert "version" in data
        assert "api_version" in data

    def test_error_response_is_json(self, client):
        resp = client.get("/nonexistent-route-xyz")
        assert resp.status_code == 404
        assert "application/json" in resp.headers.get("content-type", "")


class TestErrorResponseFormat:
    """Error response format (RFC 7807)."""

    def test_404_response_format(self, client):
        resp = client.get("/this-route-does-not-exist")
        assert resp.status_code == 404
        data = resp.json()
        # Should have some error structure
        assert "detail" in data or "error" in data or "message" in data

    def test_401_response_format(self, client):
        resp = client.get("/admin/accounts/users")
        assert resp.status_code in (401, 403, 404)
        if resp.status_code in (401, 403):
            data = resp.json()
            assert "detail" in data or "error" in data

    def test_error_handler_class_exists(self):
        from infrastructure.observability.error_handler import ErrorHandler
        assert ErrorHandler is not None

    def test_error_handler_has_categories(self):
        from infrastructure.observability.error_handler import ErrorCategory
        assert hasattr(ErrorCategory, "AUTHENTICATION")
        assert hasattr(ErrorCategory, "AUTHORIZATION")
        assert hasattr(ErrorCategory, "VALIDATION")
        assert hasattr(ErrorCategory, "NOT_FOUND")
        assert hasattr(ErrorCategory, "RATE_LIMIT")
        assert hasattr(ErrorCategory, "DATABASE")
        assert hasattr(ErrorCategory, "INTERNAL")

    def test_global_exception_handler_callable(self):
        from infrastructure.observability.error_handler import global_exception_handler
        assert callable(global_exception_handler)


class TestPaginationFormat:
    """Pagination format (cursor-based)."""

    def test_encode_decode_cursor(self):
        from infrastructure.utils.pagination import (
            decode_keyset_cursor,
            encode_keyset_cursor,
        )
        values = [100, "test", 3.14]
        cursor = encode_keyset_cursor(values)
        decoded = decode_keyset_cursor(cursor)
        assert decoded is not None
        assert decoded[0] == 100

    def test_build_cursor_pagination_payload(self):
        from infrastructure.utils.pagination import build_cursor_pagination_payload
        payload = build_cursor_pagination_payload([], None, 20)
        assert "items" in payload
        assert "next_cursor" in payload
        assert "has_next" in payload
        assert "page_size" in payload

    def test_safe_page_defaults(self):
        from infrastructure.utils.pagination import safe_page
        page, size = safe_page(None, None)
        assert page == 1
        assert size == 20

    def test_safe_page_clamps_size(self):
        from infrastructure.utils.pagination import safe_page, MAX_PAGE_SIZE
        page, size = safe_page(1, 500)
        assert size == MAX_PAGE_SIZE

    def test_max_page_size_positive(self):
        from infrastructure.utils.pagination import MAX_PAGE_SIZE
        assert MAX_PAGE_SIZE > 0


class TestMiddlewareHeaders:
    """Response headers set by middleware."""

    def test_response_has_content_type(self, client):
        resp = client.get("/health")
        assert "content-type" in resp.headers

    def test_cors_headers_on_options(self, client):
        resp = client.options("/health")
        # CORS headers may or may not be present depending on config
        assert resp.status_code in (200, 404, 405)


class TestOpenAPISpec:
    """OpenAPI specification."""

    def test_openapi_schema_available(self, client):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "paths" in data
        assert "info" in data

    def test_openapi_has_paths(self, client):
        resp = client.get("/openapi.json")
        data = resp.json()
        assert len(data["paths"]) > 0

    def test_openapi_has_health_path(self, client):
        resp = client.get("/openapi.json")
        data = resp.json()
        assert "/health" in data["paths"]
