"""FILE-95 / TF-211..TF-214 — Law 23 + Law 21 audit-column contract for the
tables declared in ``domains/hr/models/employee_models.py``.

The audit that produced TF-211..TF-214 inspected the **deployed database**
(``_audit/logs/07_tables_fields.jsonl`` records ``table: hr.employee_biometrics``
and ``table: hr.geo_fence_logs`` with empty ``model_file``) rather than the ORM
source. The ORM models were already correct; the *migrations* that create those
two tables were not. ``20260806_0003_baseline_sync_orm_tables`` builds both
``hr.employee_biometrics`` (line 2057) and ``hr.geo_fence_logs`` (line 2810)
from a truncated column list that omits ``created_at``/``updated_at``, and no
later migration re-adds them. Every INSERT issued through the ORM therefore
fails with SQLSTATE 42703 (column does not exist).

Two layers are asserted here:

1. *ORM layer* (always runs, no database needed) — Law 23/Law 21 on the model,
   plus the "declared exactly once" invariant that proves the duplicated
   ``created_at``/``updated_at``/``country_code`` class-body assignments are
   gone.
2. *Database layer* (runs only when a live PostgreSQL is reachable) —
   ``information_schema.columns`` must contain every column the ORM declares,
   which is the operational form of the ``db/tables`` nature check.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[4]
_BACKEND_ROOT = _REPO_ROOT / "backend"
_MODEL_FILE = _BACKEND_ROOT / "domains" / "hr" / "models" / "employee_models.py"

# The two tables the audit named (TF-211..TF-214).
_TABLES_UNDER_FINDING = {
    "hr.employee_biometrics": "EmployeeBiometric",
    "hr.geo_fence_logs": "GeoFenceLog",
}

# Law 23 — the standard column set every model must carry.
_AUDIT_COLUMNS = ("created_at", "updated_at", "country_code", "is_deleted")


def _load_env() -> None:
    """Load DATABASE_URL from the repo-root or backend ``.env`` without
    overriding anything already exported by the environment."""
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - dotenv is a hard dependency
        return
    for candidate in (_REPO_ROOT / ".env", _BACKEND_ROOT / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)


_load_env()


@pytest.fixture(scope="module")
def live_columns() -> dict[str, set[str]]:
    """Map ``schema.table -> {column_name}`` from the live database.

    Returns an empty mapping (and the tests that consume it are skipped) when no
    PostgreSQL is reachable, so the suite still runs on a machine with only the
    SQLite test database available.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not set — no live database to compare against")

    from sqlalchemy import create_engine, text

    engine = create_engine(url, connect_args={"connect_timeout": 10})
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT table_schema, table_name, column_name "
                    "FROM information_schema.columns "
                    "WHERE table_schema = 'hr' "
                    "AND table_name IN ('employee_biometrics', 'geo_fence_logs')"
                )
            ).all()
    except Exception as exc:  # network/dialect problems are not test failures
        pytest.skip(f"live database not reachable ({type(exc).__name__}: {exc})")
    finally:
        engine.dispose()

    columns: dict[str, set[str]] = {}
    for schema, table, column in rows:
        columns.setdefault(f"{schema}.{table}", set()).add(column)
    return columns


# ─────────────────────────────────────────────────────────────────────────
# 1 · ORM layer
# ─────────────────────────────────────────────────────────────────────────


def _orm_tables() -> dict[str, object]:
    from infrastructure.database.base import Base

    import domains.hr.models.employee_models  # noqa: F401  (registers tables)

    return {name: table for name, table in Base.metadata.tables.items()}


@pytest.mark.parametrize("table_name", sorted(_TABLES_UNDER_FINDING))
@pytest.mark.parametrize("column", ("created_at", "updated_at"))
def test_table_under_finding_declares_audit_column(table_name: str, column: str) -> None:
    """Law 23 — the ORM model for both tables under TF-211..TF-214 carries the
    audit column. This is the half of the contract the audit could not see."""
    table = _orm_tables()[table_name]
    assert column in table.columns, f"{table_name} ORM model is missing {column}"


@pytest.mark.parametrize("table_name", sorted(_TABLES_UNDER_FINDING))
def test_table_under_finding_created_at_has_server_default(table_name: str) -> None:
    """Law 21 — timestamps use ``server_default=func.now()`` so a raw INSERT that
    omits the column still gets a value."""
    table = _orm_tables()[table_name]
    assert table.columns["created_at"].server_default is not None, (
        f"{table_name}.created_at has no server_default (Law 21)"
    )
    assert table.columns["updated_at"].server_default is not None, (
        f"{table_name}.updated_at has no server_default (Law 21)"
    )


def test_audit_columns_are_declared_exactly_once() -> None:
    """Law 23 hygiene — each class body must declare the standard columns once.

    A second ``created_at = Column(...)`` in the same class body silently
    rebinds the name: the first Column object is never registered on the Table,
    so the duplicate is invisible at runtime but hides real drift. This parses
    the module with ``ast`` because the ORM metadata cannot express it.
    """
    tree = ast.parse(_MODEL_FILE.read_text(encoding="utf-8"))

    offenders: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        seen: dict[str, int] = {}
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if isinstance(target, ast.Name) and target.id in _AUDIT_COLUMNS:
                seen[target.id] = seen.get(target.id, 0) + 1
        for column, count in seen.items():
            if count > 1:
                offenders.append(f"{node.name}.{column} declared {count}x")

    assert not offenders, "Duplicated audit-column declarations: " + ", ".join(offenders)


# ─────────────────────────────────────────────────────────────────────────
# 2 · Database layer (the actual TF-211..TF-214 defect)
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("table_name", sorted(_TABLES_UNDER_FINDING))
@pytest.mark.parametrize("column", ("created_at", "updated_at"))
def test_deployed_table_has_audit_column(
    live_columns: dict[str, set[str]], table_name: str, column: str
) -> None:
    """TF-211..TF-214 — the deployed table must carry the audit column the ORM
    declares. This is what failed before the migration existed."""
    assert table_name in live_columns, f"{table_name} is absent from the live database"
    assert column in live_columns[table_name], (
        f"{table_name} exists in the database but has no {column!r} column; the ORM "
        f"model declares it, so every INSERT through the ORM would fail with "
        f"SQLSTATE 42703"
    )


def _orm_mapped_columns(table_name: str) -> set[str]:
    """Columns the ORM actually emits in SQL for ``table_name``.

    ``domains/_mixin_compliance.py`` back-fills ``version`` (and any other
    missing canonical column) onto ``Table.columns`` as *metadata only* — its
    docstring states "runtime ORM behavior is unchanged (the underlying class
    still has its inline columns; this patch is parallel metadata)". Such a
    column has no mapper attribute and is therefore never emitted in an INSERT,
    so the SQL contract is the mapper's column set, not ``Table.columns``.
    """
    from sqlalchemy import inspect as sa_inspect

    from domains.hr.models import employee_models

    _orm_tables()  # ensure every model module is registered
    cls = getattr(employee_models, _TABLES_UNDER_FINDING[table_name])
    assert cls.__table__ is _orm_tables()[table_name], (
        f"{table_name} resolved to a different Table than expected"
    )
    return {c.key for c in sa_inspect(cls).columns}


@pytest.mark.parametrize("table_name", sorted(_TABLES_UNDER_FINDING))
def test_orm_columns_all_exist_in_deployed_table(
    live_columns: dict[str, set[str]], table_name: str
) -> None:
    """Law 6 — Alembic is the only schema source of truth, so every column the
    ORM emits must actually exist in the database."""
    missing = sorted(_orm_mapped_columns(table_name) - live_columns[table_name])
    assert not missing, (
        f"{table_name}: the ORM emits {missing} but the migration chain never "
        f"creates them (Law 6 drift — INSERT fails with SQLSTATE 42703)"
    )