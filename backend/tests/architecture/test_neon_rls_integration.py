"""Neon PostgreSQL RLS interceptor integration test (ADR-019 / ADR-028).

Mocked PG engine: confirms `install_rls_policies` only emits
`ENABLE / FORCE ROW LEVEL SECURITY` and `CREATE POLICY` SQL when the
bound dialect is PostgreSQL, and is a clean no-op on SQLite.

This does NOT require a live Neon connection — it inspects the SQL the
function would emit. The Postgres dialect handles identifier quoting
the same way for Neon and self-hosted PG, so the test is portable.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine

from infrastructure.database.rls_interceptor import (
    generate_rls_policy_sql,
    install_rls_policies,
)


# Minimal in-memory registry so tests are self-sufficient and don't rely
# on the live database introspection (which depends on the runtime
# schema_translate_map and may be empty in test contexts).
_TEST_TABLES: dict[str, str] = {
    "orders": "country_code",
    "products": "country_code",
    "supplier_profiles": "country_code",
}


def _executed_sql(mock_conn) -> list[str]:
    sqls: list[str] = []
    for call in mock_conn.execute.call_args_list:
        arg = call.args[0] if call.args else None
        if arg is None:
            continue
        sqls.append(str(arg).strip())
    return sqls


def _make_pg_engine_mock() -> tuple[MagicMock, MagicMock]:
    engine = MagicMock()
    engine.dialect.name = "postgresql"

    conn = MagicMock(name="pg_conn")
    conn.execute = MagicMock(return_value=None)

    conn_ctx = MagicMock(name="pg_conn_ctx")
    conn_ctx.__enter__ = MagicMock(return_value=conn)
    conn_ctx.__exit__ = MagicMock(return_value=False)

    connect_handle = MagicMock(name="pg_connect_handle")
    connect_handle.execution_options = MagicMock(return_value=conn_ctx)

    engine.connect = MagicMock(return_value=connect_handle)
    return engine, conn


def test_rls_skipped_on_sqlite_engine():
    """SQLite engine: install_rls_policies must short-circuit with no SQL."""
    engine = create_engine("sqlite:///var/zozi.db")
    with patch.object(engine, "connect") as connect_mock:
        install_rls_policies(engine)
        connect_mock.assert_not_called()


def test_rls_policy_sql_contains_postgres_only_statements():
    """generate_rls_policy_sql output must include CREATE POLICY statements."""
    with patch(
        "infrastructure.database.rls_interceptor.COUNTRY_AWARE_TABLES",
        _TEST_TABLES,
    ):
        sql = generate_rls_policy_sql(schema="public")
    assert "CREATE POLICY" in sql
    assert "USING (" in sql
    # Every test table appears in the generated SQL
    for table in _TEST_TABLES.keys():
        assert table in sql, f"Expected policy for {table}"


def test_rls_installer_emits_enable_and_create_policy_on_postgres():
    """Mocked Postgres connection: confirm ENABLE / FORCE / CREATE POLICY SQL."""
    engine, conn = _make_pg_engine_mock()
    with patch(
        "infrastructure.database.rls_interceptor.COUNTRY_AWARE_TABLES",
        _TEST_TABLES,
    ):
        install_rls_policies(engine)
    sqls = _executed_sql(conn)
    joined = "\n".join(sqls)
    assert "ENABLE ROW LEVEL SECURITY" in joined
    assert "FORCE ROW LEVEL SECURITY" in joined
    assert "CREATE POLICY" in joined
    # Each table in the test registry gets its own ALTER TABLE statements
    for table in _TEST_TABLES.keys():
        assert table in joined


def test_neon_url_is_treated_as_postgres_dialect():
    """``postgresql+asyncpg://...neon.tech/zozi`` is a Postgres dialect.

    install_rls_policies() must proceed (not return early) when the
    engine.dialect.name == "postgresql", since Neon uses the standard
    postgres dialect under the asyncpg driver.
    """
    engine, conn = _make_pg_engine_mock()
    with patch(
        "infrastructure.database.rls_interceptor.COUNTRY_AWARE_TABLES",
        _TEST_TABLES,
    ):
        install_rls_policies(engine)
    assert conn.execute.called, "Postgres dialect should invoke SQL execution"
    joined = "\n".join(_executed_sql(conn))
    assert "ENABLE ROW LEVEL SECURITY" in joined
    assert "CREATE POLICY" in joined


def test_neon_pool_kwargs_match_adr019_budget():
    """Sanity: Neon pool config respects ADR-019 limits when env unset.

    Env-overridable defaults — the function reads DB_POOL_SIZE /
    DB_MAX_OVERFLOW / DB_POOL_RECYCLE at call time. The hard-coded
    defaults in the function body are pool_size=10, max_overflow=5,
    pool_recycle=300 per ADR-019 / ADR-028.
    """
    import os

    from infrastructure.database.database import _build_neon_pool_kwargs

    saved = {k: os.environ.pop(k, None) for k in ("DB_POOL_SIZE", "DB_MAX_OVERFLOW", "DB_POOL_RECYCLE")}
    try:
        kwargs = _build_neon_pool_kwargs()
        assert kwargs["pool_size"] == 10, kwargs
        assert kwargs["max_overflow"] == 5, kwargs
        assert kwargs["pool_recycle"] == 300, kwargs
        assert kwargs["pool_pre_ping"] is True
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v


def test_neon_detection_via_substring():
    """``_is_neon_url()`` returns True for any URL containing ``neon.tech``."""
    from infrastructure.database.database import _is_neon_url, _enforce_neon_ssl

    assert _is_neon_url("postgresql://u:p@ep-foo-123.neon.tech/zozi")
    assert _is_neon_url("postgresql+asyncpg://u:p@ep-foo-123.neon.tech/zozi")
    assert _is_neon_url("postgresql://u:p@neon-http.foo/bar")
    assert not _is_neon_url("postgresql://u:p@localhost:5432/zozi")
    assert not _is_neon_url("sqlite:///var/zozi.db")

    enforced = _enforce_neon_ssl("postgresql://u:p@ep-x.neon.tech/zozi?sslmode=verify-full")
    assert "sslmode=require" in enforced
    assert "verify-full" not in enforced

    enforced_async = _enforce_neon_ssl("postgresql+asyncpg://u:p@ep-x.neon.tech/zozi")
    assert "ssl=require" in enforced_async
    assert "sslmode=" not in enforced_async