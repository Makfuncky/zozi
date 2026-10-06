"""Tier 0 RLS interceptor regression tests.

``infrastructure/database/rls_interceptor.py`` defined ``instrument_rls``
twice. The second, minimal definition shadowed the first, so the version that
actually ran never inspected the database and never populated
``COUNTRY_AWARE_TABLES``. The registry stayed empty, which meant the
``before_execute`` backstop matched no tables and silently filtered nothing:
tenant isolation had no working application-level enforcement at all.

These tests lock the wiring in, and verify the backstop actually constrains a
query once a scope is set.
"""
from __future__ import annotations

import inspect

import pytest
from sqlalchemy import select

from infrastructure.database.base import Base
from infrastructure.database.rls_interceptor import (
    COUNTRY_AWARE_TABLES,
    SecurityContextMissingError,
    _extract_table_names,
    instrument_rls,
    rls_before_execute,
    rls_is_restricted_ctx,
    rls_country_scope_ctx,
    set_rls_context,
    clear_rls_context,
)


def _table_by_bare_name(name: str):
    """Look up a Table by bare name; metadata keys are schema-qualified."""
    if name in Base.metadata.tables:
        return Base.metadata.tables[name]
    for table in Base.metadata.tables.values():
        if table.name == name:
            return table
    return None


def test_instrument_rls_is_not_shadowed_by_a_stub():
    """The effective instrument_rls must populate the registry.

    A duplicate definition is the exact failure mode that disabled tenant
    isolation, so assert the *behaviour* of the bound symbol rather than
    counting definitions.
    """
    src = inspect.getsource(instrument_rls)
    assert "COUNTRY_AWARE_TABLES.update" in src, (
        "instrument_rls must merge DB-derived country-aware tables; the "
        "effective implementation is a shadowing stub"
    )


def test_instrument_rls_populates_registry_from_live_database(tmp_path):
    """After instrumenting a real engine the registry must be non-empty."""
    from sqlalchemy import create_engine

    engine = create_engine(f"sqlite:///{tmp_path / 'rls.db'}")
    Base.metadata.create_all(engine)

    import infrastructure.database.rls_interceptor as mod

    saved = dict(mod.COUNTRY_AWARE_TABLES)
    mod.COUNTRY_AWARE_TABLES.clear()
    try:
        assert mod.COUNTRY_AWARE_TABLES == {}, "precondition: registry starts empty"
        instrument_rls(engine)
        assert mod.COUNTRY_AWARE_TABLES, (
            "instrument_rls left COUNTRY_AWARE_TABLES empty, so the "
            "before_execute backstop can never filter any table"
        )
        for table_name, column_name in mod.COUNTRY_AWARE_TABLES.items():
            assert column_name == "country_code"
            assert _table_by_bare_name(table_name) is not None, (
                f"registry references unknown table {table_name}"
            )
    finally:
        mod.COUNTRY_AWARE_TABLES.clear()
        mod.COUNTRY_AWARE_TABLES.update(saved)


def test_extract_table_names_finds_the_from_table():
    """The table-name extraction the backstop relies on must work."""
    table = _table_by_bare_name("orders")
    if table is None:  # pragma: no cover - orders always present in this repo
        pytest.skip("orders table not registered")
    clause = select(table).where(table.c.id == 1)
    names = _extract_table_names(clause)
    assert "orders" in names


def test_backstop_raises_when_restricted_without_scope():
    """Restricted query on a country-aware table without a scope must fail."""
    table = _table_by_bare_name("orders")
    if table is None:  # pragma: no cover
        pytest.skip("orders table not registered")

    import infrastructure.database.rls_interceptor as mod

    saved = dict(mod.COUNTRY_AWARE_TABLES)
    mod.COUNTRY_AWARE_TABLES["orders"] = "country_code"
    token_scope = rls_country_scope_ctx.set(None)
    token_restricted = rls_is_restricted_ctx.set(True)
    try:
        clause = select(table).where(table.c.id == 1)
        with pytest.raises(SecurityContextMissingError):
            rls_before_execute(None, clause, None, None, None)
    finally:
        rls_country_scope_ctx.reset(token_scope)
        rls_is_restricted_ctx.reset(token_restricted)
        mod.COUNTRY_AWARE_TABLES.clear()
        mod.COUNTRY_AWARE_TABLES.update(saved)


def test_backstop_injects_country_filter_when_scoped():
    """With a scope set, the country predicate must be injected."""
    table = _table_by_bare_name("orders")
    if table is None:  # pragma: no cover
        pytest.skip("orders table not registered")

    import infrastructure.database.rls_interceptor as mod

    saved = dict(mod.COUNTRY_AWARE_TABLES)
    mod.COUNTRY_AWARE_TABLES["orders"] = "country_code"
    token_scope = rls_country_scope_ctx.set(frozenset({"NG"}))
    token_restricted = rls_is_restricted_ctx.set(True)
    try:
        clause = select(table).where(table.c.id == 1)
        new_clause, _mp, _p = rls_before_execute(None, clause, None, None, None)
        rendered = str(new_clause)
        assert "country_code" in rendered, (
            f"expected an injected country_code predicate, got: {rendered}"
        )
    finally:
        rls_country_scope_ctx.reset(token_scope)
        rls_is_restricted_ctx.reset(token_restricted)
        mod.COUNTRY_AWARE_TABLES.clear()
        mod.COUNTRY_AWARE_TABLES.update(saved)


def test_unrestricted_context_is_a_pass_through():
    """Default (unrestricted) context must not alter the statement."""
    table = _table_by_bare_name("orders")
    if table is None:  # pragma: no cover
        pytest.skip("orders table not registered")

    token_scope = rls_country_scope_ctx.set(None)
    token_restricted = rls_is_restricted_ctx.set(False)
    try:
        clause = select(table).where(table.c.id == 1)
        out, mp, p = rls_before_execute(None, clause, None, None, None)
        assert out is clause
    finally:
        rls_country_scope_ctx.reset(token_scope)
        rls_is_restricted_ctx.reset(token_restricted)


def test_validate_rls_coverage_reports_no_drift_on_a_live_db(tmp_path):
    """Registry entries must resolve against the real schema."""
    from sqlalchemy import create_engine

    engine = create_engine(f"sqlite:///{tmp_path / 'cov.db'}")
    Base.metadata.create_all(engine)

    import infrastructure.database.rls_interceptor as mod

    saved = dict(mod.COUNTRY_AWARE_TABLES)
    mod.COUNTRY_AWARE_TABLES.clear()
    try:
        instrument_rls(engine)
        issues = mod.validate_rls_coverage(engine)
        assert issues == [], f"RLS coverage drift detected: {issues[:10]}"
    finally:
        mod.COUNTRY_AWARE_TABLES.clear()
        mod.COUNTRY_AWARE_TABLES.update(saved)
