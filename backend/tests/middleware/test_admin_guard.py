"""Tests for the server-side admin guard middleware.

These tests verify that:

- ``is_admin_path`` correctly identifies admin-namespace paths
- ``is_admin_role`` correctly validates the role string
- ``AdminGuardMiddleware`` returns 403 when the user is unauthenticated
- ``AdminGuardMiddleware`` returns 403 when the user is a non-admin
- ``AdminGuardMiddleware`` lets admin users through
- Non-admin paths are not affected
- Login/health endpoints under the admin namespace are allowlisted
"""
from __future__ import annotations

import importlib

import pytest


def _import_guard():
    return importlib.import_module("middleware.admin_guard_middleware")


class _State:
    """A tiny namespace used in place of ``request.state`` for tests."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _URL:
    def __init__(self, path: str):
        self.path = path


class _Request:
    def __init__(self, path: str, state: _State | None = None):
        self.url = _URL(path)
        self.state = state or _State()


@pytest.mark.parametrize(
    "path",
    [
        "/admin",
        "/admin/",
        "/admin/orders",
        "/admin/orders/123",
        "/api/v1/admin",
        "/api/v1/admin/",
        "/api/v1/admin/orders",
        "/api/v1/admin/finance/invoices",
    ],
)
def test_is_admin_path_matches_admin_paths(path: str) -> None:
    guard = _import_guard()
    assert guard.is_admin_path(path) is True


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/api/v1/products",
        "/api/v1/customer/orders",
        "/api/v1/supplier/profile",
        "/health",
        "/docs",
        "/openapi.json",
    ],
)
def test_is_admin_path_skips_non_admin_paths(path: str) -> None:
    guard = _import_guard()
    assert guard.is_admin_path(path) is False


@pytest.mark.parametrize(
    "path",
    [
        "/admin/login",
        "/admin/login/",
        "/admin/health",
        "/api/v1/admin/login",
        "/api/v1/admin/login/",
        "/api/v1/admin/health",
    ],
)
def test_is_admin_path_allowlists_login_and_health(path: str) -> None:
    guard = _import_guard()
    assert guard.is_admin_path(path) is False


@pytest.mark.parametrize("path", ["/admin", "/api/v1/admin"])
def test_is_admin_path_treats_bare_admin_prefix_as_admin(path: str) -> None:
    guard = _import_guard()
    assert guard.is_admin_path(path) is True


@pytest.mark.parametrize(
    "role",
    ["admin", "Admin", "ADMIN", "super_admin", "superadmin", "SUPER_ADMIN"],
)
def test_is_admin_role_accepts_admin_roles(role: str) -> None:
    guard = _import_guard()
    assert guard.is_admin_role(role) is True


@pytest.mark.parametrize("role", ["customer", "supplier", "logistics", "guest", "employee", None, "", "  "])
def test_is_admin_role_rejects_non_admin_roles(role) -> None:
    guard = _import_guard()
    assert guard.is_admin_role(role) is False


@pytest.mark.asyncio
async def test_admin_guard_blocks_unauthenticated_request() -> None:
    guard = _import_guard()
    mw = guard.AdminGuardMiddleware(app=None)
    request = _Request("/admin/orders", state=_State(user_role=None, user_id=None))

    async def _call_next(_req):
        raise AssertionError("call_next must not be invoked for blocked requests")

    response = await mw.dispatch(request, _call_next)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_guard_blocks_customer_with_admin_path() -> None:
    guard = _import_guard()
    mw = guard.AdminGuardMiddleware(app=None)
    request = _Request(
        "/api/v1/admin/orders",
        state=_State(user_role="customer", user_id=42),
    )

    async def _call_next(_req):
        raise AssertionError("call_next must not be invoked for blocked requests")

    response = await mw.dispatch(request, _call_next)
    assert response.status_code == 403
    body = response.body.decode("utf-8")
    assert "Admin access required" in body


@pytest.mark.asyncio
async def test_admin_guard_allows_admin_user() -> None:
    guard = _import_guard()
    mw = guard.AdminGuardMiddleware(app=None)
    request = _Request(
        "/admin/orders",
        state=_State(user_role="admin", user_id=1),
    )

    sentinel = object()

    async def _call_next(_req):
        return sentinel

    result = await mw.dispatch(request, _call_next)
    assert result is sentinel


@pytest.mark.asyncio
async def test_admin_guard_passes_non_admin_path_through() -> None:
    guard = _import_guard()
    mw = guard.AdminGuardMiddleware(app=None)
    request = _Request(
        "/api/v1/products",
        state=_State(user_role="customer", user_id=7),
    )

    sentinel = object()

    async def _call_next(_req):
        return sentinel

    result = await mw.dispatch(request, _call_next)
    assert result is sentinel


@pytest.mark.asyncio
async def test_admin_guard_registered_in_orchestrator() -> None:
    """The guard must be part of the orchestrator's authentication layer."""
    from middleware import orchestrator
    assert orchestrator.AdminGuardMiddleware in orchestrator._AUTHENTICATION


def test_unauthenticated_admin_request_returns_403_not_500() -> None:
    """HTTP-level regression: an unauthenticated GET to /admin/* must return
    a clean 403 (with JSON body), never 500 — even when the request carries
    no Authorization header and no role information.

    Phase 5G regression surfaced a 500 here; Phase 5I verifies the fix by
    exercising the full FastAPI pipeline through a TestClient.
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from middleware.admin_guard_middleware import AdminGuardMiddleware

    app = FastAPI()
    app.add_middleware(AdminGuardMiddleware)

    @app.get("/admin/anything")
    async def admin_anything():
        return {"ok": True}

    @app.get("/admin/dashboard")
    async def admin_dashboard():
        return {"ok": True}

    @app.get("/api/v1/admin/orders")
    async def admin_orders():
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)

    for path in ("/admin/anything", "/admin/dashboard", "/api/v1/admin/orders"):
        resp = client.get(path)
        assert resp.status_code == 403, (
            f"Expected 403 for unauthenticated {path}, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body.get("code") == "admin_required"
        assert "Admin access required" in body.get("detail", "")


def test_login_and_health_admin_paths_remain_accessible_without_auth() -> None:
    """Login and health endpoints under /admin must NOT be blocked, even
    without an authenticated session — they're how users start the flow.
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from middleware.admin_guard_middleware import AdminGuardMiddleware

    app = FastAPI()
    app.add_middleware(AdminGuardMiddleware)

    @app.get("/admin/login")
    async def admin_login():
        return {"login": True}

    @app.get("/admin/health")
    async def admin_health():
        return {"status": "ok"}

    client = TestClient(app, raise_server_exceptions=False)
    for path in ("/admin/login", "/admin/health"):
        resp = client.get(path)
        assert resp.status_code == 200, (
            f"Expected 200 for {path}, got {resp.status_code}: {resp.text}"
        )
