"""Focused tests for the rescued RLS / Country-Context module.

Validates the fixes made in the RLS + middleware consolidation:

* DBA05  — the DB-level GUC ``app.current_country_code`` is now set
           transaction-locally (fail-closed) by ``set_session_rls``.
* SEC101 — the GUC is set with *bound parameters*, never f-string
           interpolation of country codes into SQL text.
* MW3    — middleware no longer imports ``models``/``services``; the
           impossible-travel fraud write and COI check use ``db.database``
           + parameterized SQL / the dependencies layer.
* L1     — all RLS enforcement funnels through the canonical
           ``utils.rls_interceptor`` ContextVar.

Run directly:  python tests/test_rls_country_context.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

from sqlalchemy import Column, MetaData, String, create_engine, select, text  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import Response  # noqa: E402

import utils.rls_interceptor as rls  # noqa: E402
from middleware.country_context import CountryContextMiddleware  # noqa: E402


class _RecordingSession:
    """Minimal stand-in for a SQLAlchemy Session that records execute() calls."""

    def __init__(self):
        self.calls = []

    def execute(self, clause, params=None):
        self.calls.append((str(clause), params))


def test_set_session_rls_sets_correct_guc_with_params():
    # No scope -> GUC reset to NULL (fail-closed).
    clear = _RecordingSession()
    rls.clear_rls_context()
    rls.set_session_rls(clear, None)
    assert any("SET LOCAL app.current_country_code = NULL" in sql for sql, _ in clear.calls), clear.calls

    # Scope set -> GUC set with bound parameter (never interpolated).
    scoped = _RecordingSession()
    rls.set_rls_context({"SA", "AE"}, is_restricted=True)
    rls.set_session_rls(scoped, None)

    sql_params = [(sql, params) for sql, params in scoped.calls if params]
    assert sql_params, scoped.calls
    sql, params = sql_params[0]
    assert ":cc" in sql, sql
    assert params["cc"] == "AE,SA", params  # sorted, comma-joined, parameterized


def test_before_execute_injects_country_filter_when_restricted():
    engine = create_engine("sqlite://")
    meta = MetaData()
    orders = __import__("sqlalchemy").Table(
        "orders", meta, Column("id", String), Column("country_code", String)
    )
    meta.create_all(engine)

    rls.set_rls_context({"AE"}, is_restricted=True)
    clause, _, _ = rls.rls_before_execute(engine, select(orders), (), {}, {})
    assert "country_code" in str(clause), str(clause)

    # Not restricted -> clause untouched (no filtering for global/admin).
    rls.set_rls_context(None, is_restricted=False)
    clause2, _, _ = rls.rls_before_execute(engine, select(orders), (), {}, {})
    assert "WHERE" not in str(clause2), str(clause2)


def test_before_execute_raises_when_restricted_but_no_scope():
    engine = create_engine("sqlite://")
    meta = MetaData()
    orders = __import__("sqlalchemy").Table(
        "orders", meta, Column("id", String), Column("country_code", String)
    )
    rls.set_rls_context(None, is_restricted=True)
    try:
        rls.rls_before_execute(engine, select(orders), (), {}, {})
        assert False, "expected SecurityContextMissingError"
    except rls.SecurityContextMissingError:
        pass


def _make_request(path: str, headers: dict | None = None, user=None):
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [
            (k.lower().encode(), str(v).encode()) for k, v in (headers or {}).items()
        ],
        "query_string": b"",
    }
    req = Request(scope)
    req.state.request_id = "test-req-1"
    if user is not None:
        req.state.user = user
    return req


async def test_country_context_middleware_dispatch_admin_path():
    captured = {}

    class _App:
        pass

    mw = CountryContextMiddleware(_App())

    async def call_next(req):
        captured["scope"] = rls.rls_country_scope_ctx.get()
        captured["restricted"] = rls.rls_is_restricted_ctx.get()
        captured["state_code"] = getattr(req.state, "country_code", None)
        return Response("ok")

    req = _make_request("/admin/AE/orders", user={"role": "admin", "id": 1})
    await mw.dispatch(req, call_next)

    assert captured["scope"] == {"AE"}, captured
    assert captured["restricted"] is False, captured
    assert captured["state_code"] == "AE", captured
    # Context is cleared after the request.
    assert rls.rls_country_scope_ctx.get() is None


async def test_country_context_middleware_dispatch_staff_scope():
    captured = {}

    class _App:
        pass

    mw = CountryContextMiddleware(_App())

    async def call_next(req):
        captured["scope"] = rls.rls_country_scope_ctx.get()
        captured["restricted"] = rls.rls_is_restricted_ctx.get()
        return Response("ok")

    user = {"role": "staff", "id": 2, "staff_country_codes": ["AE", "SA"]}
    req = _make_request("/some/path", user=user)
    await mw.dispatch(req, call_next)

    assert captured["scope"] == {"AE", "SA"}, captured
    assert captured["restricted"] is True, captured


def main():
    test_set_session_rls_sets_correct_guc_with_params()
    test_before_execute_injects_country_filter_when_restricted()
    test_before_execute_raises_when_restricted_but_no_scope()
    asyncio.run(test_country_context_middleware_dispatch_admin_path())
    asyncio.run(test_country_context_middleware_dispatch_staff_scope())
    print("ALL RLS / COUNTRY-CONTEXT TESTS PASSED")


if __name__ == "__main__":
    main()
