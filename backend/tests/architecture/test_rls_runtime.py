"""Phase 7C — Runtime RLS enforcement at request time (Law 5).

Verifies that:
  1. ``set_rls_context`` is invoked per-request by CountryContextMiddleware
     for authenticated users with a ``staff_country_codes`` JWT claim.
  2. ``clear_rls_context`` is invoked after the response so the ContextVar
     does not leak across requests handled on the same async task.
  3. The RLS ``before_execute`` interceptor restricts SELECTs against
     country-aware tables (``catalog.products``) to the requested scope
     when ``is_restricted=True``.
  4. Unrestricted roles (``admin``, ``super_admin``) bypass the country
     filter so they can audit cross-country data.
  5. Cross-country queries without a scope raise ``SecurityContextMissingError``.
  6. The ``country_staff_assignments`` seed (canonical Python module) has
     AE+SA assignments for every demo user so login flows can resolve a
     non-empty scope.
  7. The duplicate ``instrument_rls`` symbol that previously shadowed the
     country-aware derivation is gone (a single definition remains).
"""
from __future__ import annotations

from pathlib import Path

import pytest


_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
# Canonical Python module — replaces the legacy ``country_staff_assignments_full.json``.
from infrastructure.database.seed import _seed_constants
_RLS_PATH = _BACKEND_ROOT / "infrastructure" / "database" / "rls_interceptor.py"


# ─────────────────────────────────────────────────────────────────────
# Task 4 — country_staff_assignments seed
# ─────────────────────────────────────────────────────────────────────


class TestCountryStaffSeedCompleteness:
    """Every demo user (admin/supplier/customer) must have entries for BOTH AE and SA."""

    def _load_seed(self) -> dict:
        return _seed_constants.COUNTRY_STAFF_ASSIGNMENTS

    def test_seed_constants_module_exists(self):
        """Canonical Python seed constants module must exist (replaces JSON)."""
        assert hasattr(_seed_constants, "COUNTRY_STAFF_ASSIGNMENTS"), (
            "infrastructure/database/seed/_seed_constants.py must define "
            "COUNTRY_STAFF_ASSIGNMENTS — seed data must live in Neon (via this "
            "module + _common.py:seed_data()), not in local JSON files."
        )
        assert len(_seed_constants.COUNTRY_STAFF_ASSIGNMENTS.get("country_staff_assignments", [])) > 0

    def test_admin_has_ae_and_sa(self):
        seed = self._load_seed()
        codes = {row["country_code"] for row in seed["country_staff_assignments"] if row["user_email"] == "admin@zozi.com"}
        assert codes == {"AE", "SA"}, f"admin@zozi.com assignments must cover AE and SA, got {codes}"

    def test_supplier_has_ae_and_sa(self):
        seed = self._load_seed()
        codes = {row["country_code"] for row in seed["country_staff_assignments"] if row["user_email"] == "supplier@zozi.com"}
        assert codes == {"AE", "SA"}, f"supplier@zozi.com assignments must cover AE and SA, got {codes}"

    def test_customer_has_ae_and_sa(self):
        seed = self._load_seed()
        codes = {row["country_code"] for row in seed["country_staff_assignments"] if row["user_email"] == "customer@zozi.com"}
        assert codes == {"AE", "SA"}, f"customer@zozi.com assignments must cover AE and SA, got {codes}"


# ─────────────────────────────────────────────────────────────────────
# Task 1 — RLS infrastructure sanity
# ─────────────────────────────────────────────────────────────────────


class TestRLSInfrastructure:
    """Sanity-check the RLS interceptor module."""

    def test_set_rls_context_stores_scope(self):
        from infrastructure.database.rls_interceptor import (
            set_rls_context,
            rls_country_scope_ctx,
            rls_is_restricted_ctx,
            clear_rls_context,
        )
        clear_rls_context()
        set_rls_context({"AE"}, is_restricted=True)
        assert rls_country_scope_ctx.get() == frozenset({"AE"})
        assert rls_is_restricted_ctx.get() is True
        clear_rls_context()

    def test_clear_rls_context_resets(self):
        from infrastructure.database.rls_interceptor import (
            set_rls_context,
            rls_country_scope_ctx,
            clear_rls_context,
        )
        set_rls_context({"SA"}, is_restricted=True)
        clear_rls_context()
        assert rls_country_scope_ctx.get() is None

    def test_no_duplicate_instrument_rls(self):
        """The earlier duplicate ``instrument_rls`` shadowed the country-aware derivation."""
        source = _RLS_PATH.read_text(encoding="utf-8")
        assert source.count("def instrument_rls") == 1, (
            "rls_interceptor.py must declare exactly one instrument_rls symbol"
        )


# ─────────────────────────────────────────────────────────────────────
# Task 3 — CountryContextMiddleware wires set/clear per request
# ─────────────────────────────────────────────────────────────────────


class _StubUser:
    def __init__(self, user_id: int, role: str, staff_country_codes=None):
        self.id = user_id
        self.role = role
        self.staff_country_codes = staff_country_codes or []


class _StubRequest:
    def __init__(self, headers=None, path="/api/v1/products"):
        self.headers = headers or {}
        self.state = type("_S", (), {})()
        self.url = type("_U", (), {"path": path})()


@pytest.fixture
def rls_seed_session(db_session, engine, monkeypatch):
    """Seed the per-test ``db_session`` with two-country product rows so the
    RLS interceptor has something to filter.

    Uses raw SQL for the inserts (FKs may be stripped during test setup)
    and SQLAlchemy Core ``select()`` for the verification queries so the
    RLS interceptor's ``_extract_table_names`` can resolve ``products``.
    Registers ``products`` in ``COUNTRY_AWARE_TABLES`` and installs the
    ``before_execute`` listener on the test ``engine`` because the test
    SQLite engine bypasses the prod ``instrument_rls`` registration.
    """
    from sqlalchemy import event, select
    from infrastructure.database import rls_interceptor
    monkeypatch.setitem(rls_interceptor.COUNTRY_AWARE_TABLES, "products", "country_code")
    if not getattr(rls_interceptor, "_TEST_LISTENER_INSTALLED", False):
        event.listen(engine, "before_execute", rls_interceptor.rls_before_execute, retval=True)
        rls_interceptor._TEST_LISTENER_INSTALLED = True

    # Use SQLAlchemy Core table reflection so RLS sees a structured clause.
    from sqlalchemy import MetaData, Table, Column, String, Integer
    md = MetaData()
    products = Table(
        "products", md,
        Column("id", Integer),
        Column("name", String),
        Column("slug", String),
        Column("country_code", String(2)),
    )

    from sqlalchemy import text
    db_session.execute(text(
        "INSERT INTO products (id, name, slug, price, is_active, is_deleted, country_code) "
        "VALUES "
        "(1, 'AE widget', 'ae-widget', 1.0, 1, 0, 'AE'),"
        "(2, 'SA widget', 'sa-widget', 1.0, 1, 0, 'SA'),"
        "(3, 'AE gadget', 'ae-gadget', 1.0, 1, 0, 'AE'),"
        "(4, 'SA gadget', 'sa-gadget', 1.0, 1, 0, 'SA')"
    ))
    db_session.flush()

    class _Session:
        """Wrap ``db_session`` so tests get a method that returns Core results."""
        def __init__(self, inner, products):
            self._inner = inner
            self._products = products

        def distinct_codes(self):
            stmt = select(self._products.c.country_code).distinct()
            return self._inner.execute(stmt).fetchall()

        def raises(self):
            self._inner.execute(select(self._products.c.id))

    return _Session(db_session, products)


@pytest.mark.asyncio
async def test_country_context_middleware_sets_rls_for_restricted_user():
    from infrastructure.database.rls_interceptor import (
        rls_country_scope_ctx,
        rls_is_restricted_ctx,
        clear_rls_context,
    )
    from middleware.country_context import CountryContextMiddleware

    clear_rls_context()

    middleware = CountryContextMiddleware(app=lambda *a, **kw: None)
    request = _StubRequest(headers={"Authorization": "Bearer ignored"})
    request.state.user = _StubUser(user_id=42, role="supplier", staff_country_codes=["AE", "SA"])

    async def _call_next(_req):
        # While inside the request the RLS context MUST reflect the user
        assert rls_country_scope_ctx.get() == frozenset({"AE", "SA"})
        assert rls_is_restricted_ctx.get() is True
        return type("_R", (), {})()

    await middleware.dispatch(request, _call_next)

    # And MUST be cleared after the response so the context var does not
    # leak to the next request handled by the same async task.
    assert rls_country_scope_ctx.get() is None
    assert rls_is_restricted_ctx.get() is False


@pytest.mark.asyncio
async def test_country_context_middleware_admin_is_unrestricted():
    from infrastructure.database.rls_interceptor import (
        rls_country_scope_ctx,
        rls_is_restricted_ctx,
        clear_rls_context,
    )
    from middleware.country_context import CountryContextMiddleware

    clear_rls_context()

    middleware = CountryContextMiddleware(app=lambda *a, **kw: None)
    request = _StubRequest(headers={"Authorization": "Bearer ignored"})
    request.state.user = _StubUser(user_id=1, role="admin", staff_country_codes=["AE", "SA"])

    async def _call_next(_req):
        assert rls_is_restricted_ctx.get() is False, "admin must be unrestricted"
        return type("_R", (), {})()

    await middleware.dispatch(request, _call_next)
    clear_rls_context()


# ─────────────────────────────────────────────────────────────────────
# Task 5 — Per-request enforcement against the live interceptor
# ─────────────────────────────────────────────────────────────────────


class TestRLSPerRequestEnforcement:
    """End-to-end: the interceptor injects a country filter on catalog.products."""

    def test_ae_scope_only_returns_ae_rows(self, rls_seed_session):
        from infrastructure.database.rls_interceptor import (
            set_rls_context,
            clear_rls_context,
        )
        clear_rls_context()
        set_rls_context({"AE"}, is_restricted=True)
        try:
            rows = rls_seed_session.distinct_codes()
            codes = {r[0] for r in rows if r[0] is not None}
            assert codes <= {"AE"}, f"AE scope must not leak non-AE rows; got {codes}"
        finally:
            clear_rls_context()

    def test_sa_scope_only_returns_sa_rows(self, rls_seed_session):
        from infrastructure.database.rls_interceptor import (
            set_rls_context,
            clear_rls_context,
        )
        clear_rls_context()
        set_rls_context({"SA"}, is_restricted=True)
        try:
            rows = rls_seed_session.distinct_codes()
            codes = {r[0] for r in rows if r[0] is not None}
            assert codes <= {"SA"}, f"SA scope must not leak non-SA rows; got {codes}"
        finally:
            clear_rls_context()

    def test_unrestricted_admin_sees_all(self, rls_seed_session):
        from infrastructure.database.rls_interceptor import (
            set_rls_context,
            clear_rls_context,
        )
        clear_rls_context()
        set_rls_context(None, is_restricted=False)
        try:
            rows = rls_seed_session.distinct_codes()
            codes = {r[0] for r in rows if r[0] is not None}
            assert {"AE", "SA"}.issubset(codes), f"unrestricted scope must see AE+SA; got {codes}"
        finally:
            clear_rls_context()

    def test_country_aware_query_without_scope_raises(self, rls_seed_session):
        from infrastructure.database.rls_interceptor import (
            set_rls_context,
            clear_rls_context,
            SecurityContextMissingError,
        )
        clear_rls_context()
        set_rls_context(None, is_restricted=True)
        try:
            with pytest.raises(SecurityContextMissingError):
                rls_seed_session.raises()
        finally:
            clear_rls_context()


# ─────────────────────────────────────────────────────────────────────
# Task 6 — App boot smoke
# ─────────────────────────────────────────────────────────────────────


def test_app_boots(app):
    """``app`` fixture exercises the full middleware pipeline (incl. RLS wiring)."""
    assert app is not None
    assert app.title
