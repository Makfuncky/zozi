"""add_analytics_audit_columns

Rescue the analytics module's DBA03 genuine gaps. The analytics snapshot
models (schema ``analytics``), ``admin_analytics_snapshots`` (schema ``audit``)
and ``video_analytics`` (schema ``media``) inherit ``TenantMixin`` (so they
already carry ``uuid`` + ``version`` + ``country_code`` at runtime), but were
missing the audit + soft-delete columns expected by the standard column set.

This migration adds, per table:
  - created_by, updated_by  (audit attribution)
  - is_deleted             (soft-delete signal)

``admin_analytics_snapshots`` and ``video_analytics`` also lacked
``created_at`` / ``updated_at`` (they used ``computed_at`` / only
``created_at`` respectively), so those are added where missing.

``uuid`` / ``version`` are intentionally NOT added here: they already exist via
``TenantMixin`` and the audit detector cannot see mixin-inherited columns — that
portion of DBA03 for these tables is a detector limitation, not a real gap.

Skipped on SQLite: the dev/test database is recreated via
the ORM metadata build (``Base.metadata``), which already materialises these columns from the
ORM models.
"""
from __future__ import annotations
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from alembic.migration_helpers import safe_add_column, safe_drop_column


revision: str = "20260806_0001"
down_revision: Union[str, None] = "20260805_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (schema, table) -> columns to add (name, SQLAlchemy type, kwargs)
_ANALYTICS_TABLES = [
    ("analytics", "mv_daily_sales"),
    ("analytics", "mv_monthly_sales"),
    ("analytics", "kpi_customer"),
    ("analytics", "kpi_supplier"),
    ("analytics", "kpi_country"),
    ("analytics", "kpi_revenue"),
    ("analytics", "kpi_orders"),
    ("analytics", "kpi_retention"),
    ("analytics", "kpi_conversion"),
    ("analytics", "mv_cash_position"),
    ("analytics", "mv_facet_counts"),
]

_AUDIT_COLUMNS = [
    ("created_by", sa.Integer(), {"nullable": True}),
    ("updated_by", sa.Integer(), {"nullable": True}),
    ("is_deleted", sa.Boolean(), {"nullable": False, "server_default": sa.false()}),
]

_FULL_AUDIT_COLUMNS = [
    ("created_at", sa.DateTime(timezone=True), {"nullable": False, "server_default": sa.func.now()}),
    ("updated_at", sa.DateTime(timezone=True), {"nullable": False, "server_default": sa.func.now()}),
    ("created_by", sa.Integer(), {"nullable": True}),
    ("updated_by", sa.Integer(), {"nullable": True}),
    ("is_deleted", sa.Boolean(), {"nullable": False, "server_default": sa.false()}),
]

_VIDEO_ANALYTICS_COLUMNS = [
    ("updated_at", sa.DateTime(timezone=True), {"nullable": False, "server_default": sa.func.now()}),
    ("created_by", sa.Integer(), {"nullable": True}),
    ("updated_by", sa.Integer(), {"nullable": True}),
    ("is_deleted", sa.Boolean(), {"nullable": False, "server_default": sa.false()}),
]


def _add_columns(op, schema: str, table: str, specs) -> None:
    for name, col_type, kw in specs:
        safe_add_column(op, table, sa.Column(name, col_type, **kw), schema=schema)


def _drop_columns(op, schema: str, table: str, specs) -> None:
    for name, _, _ in reversed(specs):
        safe_drop_column(op, table, name, schema=schema)


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    for schema, table in _ANALYTICS_TABLES:
        _add_columns(op, schema, table, _AUDIT_COLUMNS)

    # admin_analytics_snapshots: missing created_at/updated_at as well.
    _add_columns(op, "audit", "admin_analytics_snapshots", _FULL_AUDIT_COLUMNS)

    # video_analytics: already has created_at, needs updated_at + audit cols.
    _add_columns(op, "media", "video_analytics", _VIDEO_ANALYTICS_COLUMNS)


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    for schema, table in reversed(_ANALYTICS_TABLES):
        _drop_columns(op, schema, table, _AUDIT_COLUMNS)

    _drop_columns(op, "audit", "admin_analytics_snapshots", _FULL_AUDIT_COLUMNS)
    _drop_columns(op, "media", "video_analytics", _VIDEO_ANALYTICS_COLUMNS)
