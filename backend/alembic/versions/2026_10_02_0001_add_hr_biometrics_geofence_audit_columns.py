"""add hr.employee_biometrics / hr.geo_fence_logs audit columns

FILE-95 / TF-211..TF-214 (Law 6, Law 21, Law 23).

``20260806_0003_baseline_sync_orm_tables`` builds these two tables from a
truncated column list:

  * ``hr.employee_biometrics`` (baseline line 2057) — no ``created_at`` /
    ``updated_at``
  * ``hr.geo_fence_logs``       (baseline line 2810) — no ``created_at`` /
    ``updated_at``

No later migration re-adds them. The sibling table created immediately below
them in the same baseline (``hr.employee_certifications``) *does* carry the pair,
which is what makes the omission an isolated defect rather than a house style.

Meanwhile the ORM classes ``EmployeeBiometric`` and ``GeoFenceLog`` in
``domains/hr/models/employee_models.py`` both declare them, and the columns are
mapper-mapped, so SQLAlchemy emits them in every INSERT. The result is
SQLSTATE 42703 (``column "created_at" of relation "hr.employee_biometrics" does
not exist``) for biometric enrolment and for geofence logging — the latter is
written from ``domains/security/services/health/flat_risk_service.py`` and
``domains/hr/services/travel/travel_service.py``.

Alembic is the only schema source of truth (Law 6), so this migration closes
the gap rather than weakening the model. Column definitions mirror the ORM
exactly so ``information_schema`` and the mapper agree:

  created_at  DATETIME NOT NULL DEFAULT now()   (model: nullable=False)
  updated_at  DATETIME NULL     DEFAULT now()   (model: nullable=True)

``version`` is deliberately NOT added: ``domains/_mixin_compliance.py`` back-fills
it onto ``Table.columns`` as metadata only, it has no mapper attribute, and it
is therefore never emitted in SQL.

Idempotent (``safe_add_column``) and a no-op on SQLite, whose test database is
rebuilt from the ORM metadata and therefore already has both columns.
Law 57 expand-contract: additive columns only, no rewrite of an applied
migration, ``downgrade`` drops exactly what ``upgrade`` added.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

from migration_helpers import safe_add_column, safe_drop_column

revision: str = "20261002_0001"
down_revision: Union[str, None] = "20261001_0001"
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None

_HR_SCHEMA = "hr"

# (schema, table) -> column specs. Mirrors ``EmployeeBiometric`` / ``GeoFenceLog``.
_TABLES: list[tuple[str, str, list[tuple[str, sa.types.TypeEngine, dict]]]] = [
    (
        _HR_SCHEMA,
        "employee_biometrics",
        [
            ("created_at", sa.DateTime(), {"nullable": False, "server_default": sa.func.now()}),
            ("updated_at", sa.DateTime(), {"nullable": True, "server_default": sa.func.now()}),
        ],
    ),
    (
        _HR_SCHEMA,
        "geo_fence_logs",
        [
            ("created_at", sa.DateTime(), {"nullable": False, "server_default": sa.func.now()}),
            ("updated_at", sa.DateTime(), {"nullable": True, "server_default": sa.func.now()}),
        ],
    ),
]


def _is_offline(conn) -> bool:
    if conn is None:
        return True
    try:
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


def _has_table(bind, schema: str, table: str) -> bool:
    if _is_offline(bind):
        raise RuntimeError("Catalog introspection unavailable in offline (--sql) mode")
    return sa_inspect(bind).has_table(table, schema=schema)


def upgrade() -> None:
    bind = op.get_bind()
    if not _is_offline(bind) and bind.dialect.name == "sqlite":
        return

    for schema, table, columns in _TABLES:
        if not _is_offline(bind) and not _has_table(bind, schema, table):
            raise RuntimeError(
                f"Cannot apply audit columns: {schema}.{table} does not exist. "
                f"Apply the baseline migrations first (Law 6)."
            )
        for name, col_type, kwargs in columns:
            safe_add_column(op, table, sa.Column(name, col_type, **kwargs), schema=schema)


def downgrade() -> None:
    bind = op.get_bind()
    if not _is_offline(bind) and bind.dialect.name == "sqlite":
        return

    for schema, table, columns in reversed(_TABLES):
        if not _is_offline(bind) and not _has_table(bind, schema, table):
            continue
        for name, _col_type, _kwargs in reversed(columns):
            safe_drop_column(op, table, name, schema=schema)