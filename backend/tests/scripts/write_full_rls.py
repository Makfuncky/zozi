#!/usr/bin/env python
"""Generate complete rls_interceptor.py"""
import sys
import os
sys.path.insert(0, '.')
os.environ['SECRET_KEY'] = 'test-key'

from data.base import Base
import data.models

content = '''from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

rls_country_scope_ctx: ContextVar[frozenset[str] | None] = ContextVar("rls_country_scope", default=None)
rls_is_restricted_ctx: ContextVar[bool] = ContextVar("rls_is_restricted", default=False)

COUNTRY_AWARE_TABLES: dict[str, str] = {
'''

for table in sorted(Base.metadata.tables.values(), key=lambda t: t.name):
    if 'country_code' in {c.name for c in table.columns}:
        content += f'    "{table.name}": "country_code",\n'

content += '''}

logger = logging.getLogger(__name__)


def derive_country_aware_tables_from_db(engine=None) -> dict[str, str]:
    """Auto-derive the country-aware registry from the LIVE database.

    Any table that actually contains a ``country_code`` column (or the explicit
    special-case columns below) is treated as country-aware. Deriving from the
    connected DB — rather than the ORM models — guarantees we never inject an RLS
    filter against a column that is absent from the table (which would raise a
    "no such column" error and break otherwise-valid queries).

    This is the automation that keeps the RLS registry honest: new country-scoped
    tables are picked up automatically per environment, and the CI drift gate
    (see ``scripts/inventory_database.py --check``) flags any divergence between
    the models, the registry, and the DB.
    """
    from sqlalchemy import inspect

    if engine is None:
        from data.db import engine as engine

    try:
        insp = inspect(engine)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("RLS auto-derivation skipped (inspector unavailable): %s", exc)
        return dict(COUNTRY_AWARE_TABLES)

    explicit_columns = {"destination_country", "code"}
    derived: dict[str, str] = {}
    for table_name in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns(table_name)}
        if "country_code" in cols:
            derived[table_name] = "country_code"
        elif table_name in COUNTRY_AWARE_TABLES and COUNTRY_AWARE_TABLES[table_name] in explicit_columns:
            derived[table_name] = COUNTRY_AWARE_TABLES[table_name]
    return derived


def validate_rls_coverage(engine=None) -> list[str]:
    """Return a list of RLS drift issues for CI.

    Flags:
      * a registry entry whose table/column is missing from the live DB
      * a model table that declares ``country_code`` but is absent from the DB
        (orphaned model column — the migration to add it has not been applied)
    """
    from sqlalchemy import inspect

    if engine is None:
        from data.db import engine as engine

    issues: list[str] = []
    try:
        insp = inspect(engine)
    except Exception as exc:  # pragma: no cover - defensive
        return [f"inspector unavailable: {exc}"]

    db_tables = set(insp.get_table_names())
    for table_name, column_name in COUNTRY_AWARE_TABLES.items():
        if table_name not in db_tables:
            continue
        cols = {c["name"] for c in insp.get_columns(table_name)}
        if column_name not in cols:
            issues.append(f"{table_name}: registry references missing column '{column_name}'")

    try:
        from data.models import Base
    except Exception:
        return issues

    for table in Base.metadata.tables.values():
        tname = table.name
        if tname not in db_tables:
            continue
        cols = {c["name"] for c in insp.get_columns(tname)}
        if "country_code" in {c.name for c in table.columns} and "country_code" not in cols:
            issues.append(f"{tname}: model declares country_code but DB column is missing")
    return issues


class SecurityContextMissingError(RuntimeError):
    """Raised when a country-aware query is executed without a security context."""


def set_rls_context(scope: set[str] | frozenset[str] | None, is_restricted: bool = True) -> None:
    rls_country_scope_ctx.set(frozenset(scope) if scope is not None else None)
    rls_is_restricted_ctx.set(is_restricted)


def clear_rls_context() -> None:
    rls_country_scope_ctx.set(None)
    rls_is_restricted_ctx.set(False)


def _extract_table_names(clause: Any) -> list[str]:
    tables: list[str] = []

    def _walk_froms(from_obj: Any) -> None:
        if hasattr(from_obj, "name"):
            tables.append(from_obj.name.lower())

        if hasattr(from_obj, "element"):
            _walk_froms(from_obj.element)
        if hasattr(from_obj, "froms"):
            for child in from_obj.froms:
                _walk_froms(child)

    if hasattr(clause, "froms"):
        for from_obj in clause.froms:
            _walk_froms(from_obj)

    return tables


def _inject_country_filter(clause: Any, table_name: str, column_name: str, scope: frozenset[str]) -> Any:
    country_column = None
    try:
        for from_obj in getattr(clause, "froms", []) or []:
            table_obj = getattr(from_obj, "element", from_obj)
            candidate = getattr(table_obj, "columns", None)
            if candidate is not None and table_obj.name.lower() == table_name and column_name in candidate:
                country_column = candidate[column_name]
                break
    except Exception:
        country_column = None

    if country_column is None:
        from sqlalchemy import sql
        table = sql.table(table_name, sql.column(column_name))
        country_column = table.columns[column_name]

    filter_condition = country_column.in_(list(scope))

    if clause.whereclause is not None:
        new_where = clause.whereclause & filter_condition
        return clause.where(new_where)
    else:
        return clause.where(filter_condition)


@event.listens_for(Engine, "before_execute", retval=True)
def rls_before_execute(conn: Any, clause: Any, multiparams: Any, params: Any, execution_options: Any, **kwargs: Any) -> tuple[Any, Any, Any]:
    scope = rls_country_scope_ctx.get()
    is_restricted = rls_is_restricted_ctx.get()

    if not is_restricted:
        return clause, multiparams, params

    table_names = _extract_table_names(clause)

    for table_name in table_names:
        if table_name not in COUNTRY_AWARE_TABLES:
            continue

        if scope is None:
            raise SecurityContextMissingError(
                f"Query targets country-aware table '{table_name}' "
                f"but no RLS country scope is set. "
                f"Call set_rls_context() before executing this query."
            )

        column_name = COUNTRY_AWARE_TABLES[table_name]
        clause = _inject_country_filter(clause, table_name, column_name, scope)

    return clause, multiparams, params


def instrument_rls(engine: Engine) -> None:
    event.listen(engine, "before_execute", rls_before_execute, retval=True)
    logger.info("RLS interceptor installed on database engine")


def generate_rls_policy_sql(schema: str = "public") -> str:
    """Generate PostgreSQL CREATE POLICY SQL for all country-aware tables.

    Each table gets a policy that restricts rows based on the
    ``auth.country_access_check(<column>)`` security-definer function.
    """
    lines: list[str] = []

    lines.append(
        "CREATE OR REPLACE FUNCTION auth.country_access_check(p_country_code TEXT)\\n"
        "RETURNS BOOLEAN AS $$\\n"
        "DECLARE\\n"
        "    v_role TEXT;\\n"
        "BEGIN\\n"
        "    SELECT current_user INTO v_role;\\n"
        "\\n"
        "    IF v_role = 'admin' OR v_role = 'postgres' OR v_role = 'service_role' THEN\\n"
        "        RETURN TRUE;\\n"
        "    END IF;\\n"
        "\\n"
        "    RETURN EXISTS (\\n"
        "        SELECT 1\\n"
        "        FROM country_staff_assignments csa\\n"
        "        WHERE csa.country_code = p_country_code\\n"
        "          AND csa.is_active = TRUE\\n"
        "          AND csa.user_id = (\\n"
        "              SELECT u.id FROM users u WHERE u.email = current_user LIMIT 1\\n"
        "          )\\n"
        "    );\\n"
        "END;\\n"
        "$$ LANGUAGE plpgsql SECURITY DEFINER;\\n"
    )

    for table_name, column_name in COUNTRY_AWARE_TABLES.items():
        policy_name = f"{table_name}_rls_policy"
        lines.append(
            f"CREATE POLICY {policy_name}\\n"
            f"    ON {schema}.{table_name}\\n"
            f"    FOR ALL\\n"
            f"    USING (\\n"
            f"        {schema}.{table_name}.{column_name} IS NULL\\n"
            f"        OR auth.country_access_check({schema}.{table_name}.{column_name})\\n"
            f"    );\\n"
        )

    return "\\n".join(lines)


def install_rls_policies(engine: Engine, schema: str = "public") -> None:
    """Enable RLS and apply policies on every country-aware Postgres table."""
    from sqlalchemy import text
    from sqlalchemy.sql import quoted_name

    safe_schema = quoted_name(schema, False)
    policy_sql = generate_rls_policy_sql(schema=schema)

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for table_name in COUNTRY_AWARE_TABLES.keys():
            safe_table = quoted_name(table_name, False)
            conn.execute(
                text(f"ALTER TABLE {safe_schema}.{safe_table} ENABLE ROW LEVEL SECURITY;")
            )
            conn.execute(text(f"ALTER TABLE {safe_schema}.{safe_table} FORCE ROW LEVEL SECURITY;"))

        conn.execute(text(policy_sql))

    logger.info("Installed RLS policies for %d tables", len(COUNTRY_AWARE_TABLES))
'''

print(content)