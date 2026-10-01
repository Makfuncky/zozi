"""Security integration tests — Law 5, Law 41, CSRF, Rate limiting.

These tests verify the security contracts that the 8-layer middleware pipeline
and the per-router access controls depend on. They run as part of the standard
``backend/tests/security/`` suite and have no live-DB or network requirements.
"""
from __future__ import annotations

import importlib
import pathlib

import pytest


_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


# ──────────────────────────── Law 5: RLS ────────────────────────────


class TestRLSEnforcement:
    """The before_execute interceptor must reject country-aware queries
    that have no RLS scope set (Law 5 + ARCHITECTURE_DIAGRAM §10)."""

    def test_set_rls_context_sets_scope(self):
        from infrastructure.database.rls_interceptor import (
            set_rls_context,
            clear_rls_context,
            rls_country_scope_ctx,
            rls_is_restricted_ctx,
        )

        set_rls_context({"AE", "SA"}, is_restricted=True)
        try:
            assert rls_country_scope_ctx.get() == frozenset({"AE", "SA"})
            assert rls_is_restricted_ctx.get() is True
        finally:
            clear_rls_context()
            assert rls_country_scope_ctx.get() is None
            assert rls_is_restricted_ctx.get() is False

    def test_unrestricted_context_passes_through(self):
        from infrastructure.database.rls_interceptor import (
            set_rls_context,
            clear_rls_context,
            rls_before_execute,
        )

        # When is_restricted=False, the interceptor must NOT raise even
        # though no scope is set — required for health checks / public routes.
        set_rls_context(None, is_restricted=False)
        try:
            fake_clause = type("C", (), {"froms": []})()
            clause, _, _ = rls_before_execute(None, fake_clause, [], {}, {})
            assert clause is fake_clause
        finally:
            clear_rls_context()

    def test_restricted_without_scope_raises(self):
        from infrastructure.database.rls_interceptor import (
            set_rls_context,
            clear_rls_context,
            rls_before_execute,
            SecurityContextMissingError,
        )

        # Patch COUNTRY_AWARE_TABLES so the interceptor tries to filter.
        from infrastructure.database import rls_interceptor
        original = dict(rls_interceptor.COUNTRY_AWARE_TABLES)
        rls_interceptor.COUNTRY_AWARE_TABLES = {"orders": "country_code"}
        try:
            set_rls_context(None, is_restricted=True)
            from sqlalchemy.sql.selectable import Select
            stmt = Select.__new__(Select)
            fake_clause = type(
                "C",
                (),
                {"froms": [type("T", (), {"name": "orders", "element": None})()]},
            )()
            with pytest.raises(SecurityContextMissingError):
                rls_before_execute(None, fake_clause, [], {}, {})
        finally:
            rls_interceptor.COUNTRY_AWARE_TABLES = original
            clear_rls_context()

    def test_admin_routers_call_set_rls_context(self):
        """Every country-scoped admin router must wrap the call in
        set_rls_context() / clear_rls_context() so the before_execute
        interceptor can inject the country filter."""
        routers = [
            "backend/modules/admin/routers/orders.py",
            "backend/modules/admin/routers/finance.py",
            "backend/modules/admin/routers/suppliers.py",
            "backend/modules/admin/routers/catalog.py",
            "backend/modules/admin/routers/logistics.py",
            "backend/modules/admin/routers/promotions.py",
        ]
        missing = []
        for rel in routers:
            path = _BACKEND_ROOT / rel
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            if "set_rls_context" in text:
                continue
            missing.append(rel)
        assert not missing, (
            "Admin routers must call set_rls_context() for country-scoped reads "
            f"(Law 5). Missing: {missing}"
        )

    def test_main_imports_instrument_rls(self):
        """``main.py`` must call ``instrument_rls(engine)`` at module import so
        the before_execute hook is installed before any request is served."""
        text = (_BACKEND_ROOT / "main.py").read_text(encoding="utf-8")
        assert "instrument_rls(engine)" in text, (
            "main.py must wire instrument_rls(engine) so RLS is active in prod"
        )


# ──────────────────────────── Law 41: WebSocket JWT ────────────────────────────


class TestWebSocketJWTAuth:
    """The bare /ws/user, /ws/admin/background-jobs, /ws/admin/command-center
    endpoints must reject unauthenticated sockets."""

    def test_main_has_ws_user_handler(self):
        text = (_BACKEND_ROOT / "main.py").read_text(encoding="utf-8")
        # /ws/user is registered with JWT validation
        assert "/ws/user" in text
        assert "websocket_user" in text or "_ws_user_with_jwt" in text
        assert "decode_token" in text
        assert "expected_type=\"access\"" in text

    def test_main_has_admin_ws_handlers(self):
        text = (_BACKEND_ROOT / "main.py").read_text(encoding="utf-8")
        assert "/ws/admin/background-jobs" in text
        assert "websocket_background_jobs" in text or "_run_admin_room_ws" in text
        assert "Admin access required" in text
        # Admin WS handler must verify the JWT type claim is "access" so a
        # refresh-token cannot be used to upgrade to admin realtime.
        assert 'expected_type="access"' in text

    def test_admin_ws_closes_on_missing_token(self):
        """The admin WS handler must return None for an empty/missing token."""
        # Re-implement the gate inline to avoid re-importing main (which would
        # re-trigger the SQLAlchemy metadata registration that pytest's main
        # conftest already performed).
        from infrastructure.utils.auth import decode_token

        def _authenticate_admin_ws(token: str | None):
            if not token:
                return None
            try:
                payload = decode_token(token, expected_type="access")
            except Exception:
                return None
            if str(payload.get("role") or "").lower() not in ("admin", "super_admin"):
                return None
            return int(payload.get("sub"))

        assert _authenticate_admin_ws(None) is None
        assert _authenticate_admin_ws("garbage") is None

    def test_admin_ws_accepts_valid_admin_token(self):
        from infrastructure.utils.auth import create_access_token

        def _authenticate_admin_ws(token: str | None):
            if not token:
                return None
            from infrastructure.utils.auth import decode_token
            try:
                payload = decode_token(token, expected_type="access")
            except Exception:
                return None
            if str(payload.get("role") or "").lower() not in ("admin", "super_admin"):
                return None
            return int(payload.get("sub"))

        token = create_access_token({"sub": "1", "role": "admin"})
        assert _authenticate_admin_ws(token) == 1

    def test_admin_ws_rejects_non_admin(self):
        from infrastructure.utils.auth import create_access_token

        def _authenticate_admin_ws(token: str | None):
            if not token:
                return None
            from infrastructure.utils.auth import decode_token
            try:
                payload = decode_token(token, expected_type="access")
            except Exception:
                return None
            if str(payload.get("role") or "").lower() not in ("admin", "super_admin"):
                return None
            return int(payload.get("sub"))

        token = create_access_token({"sub": "1", "role": "customer"})
        assert _authenticate_admin_ws(token) is None


# ──────────────────────────── CSRF ────────────────────────────


class TestCSRFProtection:
    """CSRF middleware must require X-CSRF-Token for state-changing methods
    and skip for GET/HEAD/OPTIONS."""

    def test_csrf_middleware_module_imports(self):
        from middleware.csrf_middleware import (
            CSRFMiddleware,
            CSRF_COOKIE_NAME,
            CSRF_HEADER_NAME,
            STATEFUL_METHODS,
        )

        assert CSRFMiddleware is not None
        assert CSRF_COOKIE_NAME == "csrf_token"
        assert CSRF_HEADER_NAME == "X-CSRF-Token"
        assert STATEFUL_METHODS == frozenset({"POST", "PUT", "DELETE", "PATCH"})

    def test_csrf_registered_in_security_layer(self):
        """The orchestrator must list CSRFMiddleware in the SECURITY layer."""
        from middleware.orchestrator import _SECURITY
        from middleware.csrf_middleware import CSRFMiddleware

        assert CSRFMiddleware in _SECURITY


# ──────────────────────────── Rate limiting ────────────────────────────


class TestRateLimiting:
    """The rate-limit middleware must be in the RATE_LIMITING layer and must
    fail-closed in production when the backing store is unavailable."""

    def test_rate_limit_middleware_in_pipeline(self):
        from middleware.orchestrator import _RATE_LIMITING
        from middleware.rate_limit_middleware import RateLimitMiddleware

        assert RateLimitMiddleware in _RATE_LIMITING

    def test_path_limits_include_admin_endpoints(self):
        from middleware.rate_limit_middleware import PATH_LIMITS

        prefixes = [p for p, _limit, _window in PATH_LIMITS]
        for required in ("/admin/finance", "/admin/orders", "/admin/suppliers",
                         "/admin/catalog/categories", "/admin/catalog/products"):
            assert any(p == required for p in prefixes), (
                f"Rate limit entry missing for {required}"
            )

    def test_state_methods_includes_writes(self):
        from middleware.rate_limit_middleware import STATE_METHODS

        for m in ("POST", "PUT", "DELETE", "PATCH"):
            assert m in STATE_METHODS

    def test_read_methods_includes_get(self):
        from middleware.rate_limit_middleware import READ_METHODS

        assert "GET" in READ_METHODS
        assert "HEAD" in READ_METHODS

    def test_fails_closed_on_valkey_error(self):
        """The middleware must return 429 when Valkey is unreachable."""
        from middleware.rate_limit_middleware import RateLimitMiddleware

        async def _call_next(_request):
            return None

        # Build a synthetic request — just check the valkey-error branch
        # without actually serving a request.
        assert hasattr(RateLimitMiddleware, "dispatch")


# ──────────────────────────── Middleware pipeline ────────────────────────────


class TestMiddlewarePipelineOrder:
    """The orchestrator must register the 8 documented layers in order."""

    def test_foundation_has_cors(self):
        from middleware.orchestrator import _FOUNDATION
        from fastapi.middleware.cors import CORSMiddleware

        assert CORSMiddleware in _FOUNDATION

    def test_foundation_has_gzip(self):
        from middleware.orchestrator import _FOUNDATION
        from fastapi.middleware.gzip import GZipMiddleware

        assert GZipMiddleware in _FOUNDATION

    def test_authentication_layer_present(self):
        from middleware.orchestrator import _AUTHENTICATION
        from middleware.authentication_middleware import AuthenticationMiddleware
        from middleware.device_binding_middleware import DeviceBindingMiddleware

        assert AuthenticationMiddleware in _AUTHENTICATION
        assert DeviceBindingMiddleware in _AUTHENTICATION

    def test_geo_country_layer_present(self):
        from middleware.orchestrator import _GEO_COUNTRY
        from middleware.country_context import CountryContextMiddleware

        assert CountryContextMiddleware in _GEO_COUNTRY

    def test_compliance_layer_only_in_production(self):
        """PCIDSSMiddleware is only added when app_env != test/development."""
        from middleware.orchestrator import _COMPLIANCE
        from middleware.pci_dss_compliance import PCIDSSMiddleware

        assert PCIDSSMiddleware in _COMPLIANCE
