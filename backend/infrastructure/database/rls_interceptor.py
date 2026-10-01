from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine

rls_country_scope_ctx: ContextVar[frozenset[str] | None] = ContextVar("rls_country_scope", default=None)
rls_is_restricted_ctx: ContextVar[bool] = ContextVar("rls_is_restricted", default=False)

logger = logging.getLogger(__name__)


def derive_country_aware_tables_from_db(engine=None) -> dict[str, str]:
    """Auto-derive the country-aware registry from the LIVE database."""
    try:
        from infrastructure.database.database import _engine
        actual_engine = engine or _engine
        if actual_engine is None:
            return {}
        from sqlalchemy import inspect
        inspector = inspect(actual_engine)
        result = {}
        for table_name in inspector.get_table_names():
            try:
                cols = [c["name"] for c in inspector.get_columns(table_name)]
                if "country_code" in cols:
                    result[table_name] = "country_code"
            except Exception:
                continue
        return result
    except Exception:
        return {}


def _build_country_aware_tables() -> dict[str, str]:
    try:
        return derive_country_aware_tables_from_db()
    except Exception as exc:
        logger.warning("RLS auto-derivation failed at import (%s); falling back to empty registry", exc)
        return {}


COUNTRY_AWARE_TABLES: dict[str, str] = _build_country_aware_tables()


def instrument_rls(engine: Engine, country_codes: frozenset[str] | None = None, restricted: bool = False) -> None:
    """Install RLS before_execute interceptor on the engine and populate COUNTRY_AWARE_TABLES.

    This function:
    1. Inspects the live database for tables with country_code columns
    2. Populates the COUNTRY_AWARE_TABLES registry
    3. Installs the rls_before_execute event listener (idempotent)
    """
    global COUNTRY_AWARE_TABLES

    from sqlalchemy import inspect as sa_inspect

    insp = sa_inspect(engine)

    explicit_columns = {"destination_country", "code"}
    derived: dict[str, str] = {}
    for table_name in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns(table_name)}
        if "country_code" in cols:
            derived[table_name] = "country_code"
        elif table_name in COUNTRY_AWARE_TABLES and COUNTRY_AWARE_TABLES[table_name] in explicit_columns:
            # Preserve hand-maintained special-case columns (e.g. destination_country).
            derived[table_name] = COUNTRY_AWARE_TABLES[table_name]

    # Merge: derived takes precedence, then fall back to existing registry
    COUNTRY_AWARE_TABLES.update(derived)
    logger.info("RLS: discovered %d country-aware tables", len(COUNTRY_AWARE_TABLES))

    # Install event listener (idempotent - safe to call multiple times)
    event.listen(engine, "before_execute", rls_before_execute, retval=True)
    logger.info("RLS interceptor installed on database engine")


def validate_rls_coverage(engine=None) -> list[str]:
    """Return a list of RLS drift issues for CI.

    Flags:
      * a registry entry whose table/column is missing from the live DB
      * a model table that declares ``country_code`` but is absent from the DB
        (orphaned model column — the migration to add it has not been applied)
    """
    from sqlalchemy import inspect

    if engine is None:
        from infrastructure.database.database import engine as engine

    issues: list[str] = []
    try:
        insp = inspect(engine)
    except Exception as exc:  # pragma: no cover - defensive
        return [f"inspector unavailable: {exc}"]

    db_tables = set(insp.get_table_names())
    for table_name, column_name in COUNTRY_AWARE_TABLES.items():
        if table_name not in db_tables:
            continue  # table not yet created; not a query-breaking issue
        cols = {c["name"] for c in insp.get_columns(table_name)}
        if column_name not in cols:
            issues.append(f"{table_name}: registry references missing column '{column_name}'")

    try:
        from infrastructure.database.base import Base
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

    # NOTE: Do NOT walk the WHERE clause for table names. Columns referenced in
    # the WHERE clause (e.g. `products.country_code`) would be re-resolved as a
    # second FROM entry, producing a Cartesian self-join (`FROM products, products`)
    # and "ambiguous column" errors once RLS appends its country filter.

    return tables


def _inject_country_filter(clause: Any, table_name: str, column_name: str, scope: frozenset[str]) -> Any:
    # Reuse the exact Table object already present in the query's FROM clause so the
    # injected column does not become a second (ambiguous) copy of the table.
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
        "CREATE OR REPLACE FUNCTION auth.country_access_check(p_country_code TEXT)\n"
        "RETURNS BOOLEAN AS $$\n"
        "DECLARE\n"
        "    v_role TEXT;\n"
        "BEGIN\n"
        "    SELECT current_user INTO v_role;\n"
        "\n"
        "    IF v_role = 'admin' OR v_role = 'postgres' OR v_role = 'service_role' THEN\n"
        "        RETURN TRUE;\n"
        "    END IF;\n"
        "\n"
        "    RETURN EXISTS (\n"
        "        SELECT 1\n"
        "        FROM country_staff_assignments csa\n"
        "        WHERE csa.country_code = p_country_code\n"
        "          AND csa.is_active = TRUE\n"
        "          AND csa.user_id = (\n"
        "              SELECT u.id FROM users u WHERE u.email = current_user LIMIT 1\n"
        "          )\n"
        "    );\n"
        "END;\n"
        "$$ LANGUAGE plpgsql SECURITY DEFINER;\n"
    )

    for table_name, column_name in COUNTRY_AWARE_TABLES.items():
        policy_name = _quote_ident(f"{table_name}_rls_policy")
        safe_schema = _quote_ident(schema)
        safe_table = _quote_ident(table_name)
        safe_column = _quote_ident(column_name)
        lines.append(
            f"CREATE POLICY {policy_name}\n"
            f"    ON {safe_schema}.{safe_table}\n"
            f"    FOR ALL\n"
            f"    USING (\n"
            f"        {safe_schema}.{safe_table}.{safe_column} IS NULL\n"
            f"        OR auth.country_access_check({safe_schema}.{safe_table}.{safe_column})\n"
            f"    );\n"
        )

    return "\n".join(lines)


def _quote_ident(name: str) -> str:
    """Return a safely quoted PostgreSQL identifier (double-quoted, escaped)."""
    return '"' + name.replace('"', '""') + '"'


def install_rls_policies(engine: Engine, schema: str = "public") -> None:
    """Enable RLS and apply policies on every country-aware Postgres table."""
    from sqlalchemy import text

    safe_schema = _quote_ident(schema)
    policy_sql = generate_rls_policy_sql(schema=schema)

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for table_name in COUNTRY_AWARE_TABLES.keys():
            safe_table = _quote_ident(table_name)
            conn.execute(
                text("ALTER TABLE " + safe_schema + "." + safe_table + " ENABLE ROW LEVEL SECURITY;")
            )
            conn.execute(text("ALTER TABLE " + safe_schema + "." + safe_table + " FORCE ROW LEVEL SECURITY;"))

        conn.execute(text(policy_sql))

    logger.info("Installed RLS policies for %d tables", len(COUNTRY_AWARE_TABLES))


