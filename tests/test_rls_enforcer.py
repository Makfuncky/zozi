"""Tests for the canonical RLS enforcer (backend/utils/rls_interceptor.py).

These tests assert the security-critical guarantees called out in
ARCHITECTURE_DIAGRAM.md §10.4 ("exactly one canonical RLS enforcer") and verify
the enforcer FAILS CLOSED (raises when a country-aware query runs without a scope).

Run from repo root with:
    PYTHONPATH=backend APP_ENV=test backend/venv/Scripts/python.exe -m pytest tests/test_rls_enforcer.py -q
"""

import os

os.environ.setdefault("APP_ENV", "test")

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select

from utils.rls_interceptor import (
    SecurityContextMissingError,
    clear_rls_context,
    set_rls_context,
)


def _make_engine():
    # Importing the module globally registers the before_execute listener on every
    # Engine; we rely on that (do NOT call instrument_rls, which would double-register).
    import utils.rls_interceptor  # noqa: F401

    engine = create_engine("sqlite://")
    metadata = MetaData()
    orders = Table(
        "orders",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("country_code", String(8), nullable=True),
    )
    metadata.create_all(engine)
    return engine, orders


def test_rls_injects_country_scope_and_filters_rows():
    engine, orders = _make_engine()
    with engine.begin() as conn:
        conn.execute(orders.insert().values([{"country_code": "US"}, {"country_code": "IN"}]))

    # Restricted scope -> only matching country rows must be returned.
    set_rls_context({"US"}, is_restricted=True)
    try:
        with engine.connect() as conn:
            rows = conn.execute(select(orders.c.country_code)).fetchall()
        codes = {r[0] for r in rows}
        assert codes == {"US"}, f"expected only US, got {codes}"
    finally:
        clear_rls_context()


def test_rls_fails_closed_when_restricted_without_scope():
    engine, orders = _make_engine()
    with engine.begin() as conn:
        conn.execute(orders.insert().values([{"country_code": "US"}]))

    # Restricted but NO scope set -> must raise, never silently return all rows.
    set_rls_context(None, is_restricted=True)
    try:
        raised = False
        try:
            with engine.connect() as conn:
                conn.execute(select(orders)).fetchall()
        except SecurityContextMissingError:
            raised = True
        assert raised, "RLS must fail CLOSED when restricted without a scope"
    finally:
        clear_rls_context()


def test_rls_unrestricted_returns_all_rows():
    engine, orders = _make_engine()
    with engine.begin() as conn:
        conn.execute(orders.insert().values([{"country_code": "US"}, {"country_code": "IN"}]))

    # Default (unrestricted) context -> no injection, all rows visible.
    clear_rls_context()
    with engine.connect() as conn:
        rows = conn.execute(select(orders.c.country_code)).fetchall()
    codes = {r[0] for r in rows}
    assert codes == {"US", "IN"}, f"expected all countries, got {codes}"


# Tables seeded once, globally (country_code=NULL) that must NOT be country-filtered.
# Mirrors the documented exclusion in backend/utils/rls_interceptor.py (COUNTRY_AWARE_TABLES).
GLOBAL_GL_MASTER_TABLES = {
    "accounts",
    "account_groups",
    "account_balances",
    "accruals",
    "budgets",
    "cost_centers",
    "fixed_assets",
}


def test_rls_registry_covers_all_country_scoped_models():
    """DBA05 regression: every country-scoped ORM model is in the canonical registry.

    Country-scoped tables that are missing from COUNTRY_AWARE_TABLES get NO RLS at
    either the app or DB layer (fail-open). This asserts the registry is complete
    for every model that declares a ``country_code`` column, except the documented
    global GL master tables that are intentionally shared across countries.
    """
    import data.models as _models
    from utils.rls_interceptor import COUNTRY_AWARE_TABLES

    model_tables = _models.Base.metadata.tables
    model_country_tables = {
        t.name for t in model_tables.values() if any(c.name == "country_code" for c in t.columns)
    }

    missing = model_country_tables - set(COUNTRY_AWARE_TABLES.keys())
    # Only the explicitly documented global master tables may be absent.
    unexpected = missing - GLOBAL_GL_MASTER_TABLES
    assert not unexpected, f"country-scoped tables missing RLS coverage: {sorted(unexpected)}"


def test_single_canonical_rls_definition():
    """L1 regression: there is exactly one DB-level RLS definition.

    The canonical DB-layer definition is data/pg_rls_policies.sql (zozi_rls_check,
    fed by the app.current_country_code GUC). A divergent, unused generator that
    defined a conflicting auth.country_access_check function must not exist, so the
    two definitions cannot drift apart.
    """
    import utils.rls_interceptor as rls

    for divergent in ("generate_rls_policy_sql", "install_rls_policies"):
        assert not hasattr(rls, divergent), f"{divergent} should be removed (single canonical RLS)"
