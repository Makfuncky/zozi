"""baseline_canonical_orm_schema_clean

Revision ID: b81bfc888610
Revises: 
Create Date: 2026-07-26 16:09:14.215676+00:00

This root migration materialises the canonical ORM schema in full so that
``alembic upgrade head`` can initialise a truly fresh database from scratch
(the contract enforced by CI's drift gate).
On SQLite the engine is configured with ``schema_translate_map`` (see
``alembic/env.py``) so the 16 bounded-context schemas collapse to a flat
namespace; on PostgreSQL the schemas are created natively.

Subsequent migrations apply only deltas (columns / indexes / partitions /
schema moves) and guard against objects that already exist, so they are
no-op-safe whether the database was created by this baseline or already had the
objects from a prior deployment.
"""
import os
import sys
os.environ.setdefault("ALEMBIC_MODE", "true")
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(_project_root, "alembic"))
sys.path.insert(0, _project_root)

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from data.models import Base
from migration_helpers import safe_add_column, safe_create_index, safe_drop_column, safe_drop_index
from utils.schema_compat import SCHEMA_TRANSLATE_MAP


# The 16 bounded-context schema names that models use post-0005.
_POSTGRES_SCHEMAS = sorted(SCHEMA_TRANSLATE_MAP.keys())


# revision identifiers, used by Alembic.
revision: str = 'b81bfc888610'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    bind = op.get_bind()
    return sa.inspect(bind)


def _has_table(table_name: str) -> bool:
    try:
        return table_name in _inspector().get_table_names()
    except Exception:
        return False


def _has_column(table_name: str, column_name: str) -> bool:
    try:
        return any(
            col["name"] == column_name
            for col in _inspector().get_columns(table_name)
        )
    except Exception:
        return False


def upgrade() -> None:
    # On PostgreSQL, create the 16 bounded-context schemas first so that
    # Base.metadata.create_all() (which places tables schema-qualified via
    # model __table_args__ schema=) can succeed in a fresh database where
    # the schemas do not yet exist.
    if op.get_bind().dialect.name == "postgresql":
        for sch in _POSTGRES_SCHEMAS:
            op.execute('CREATE SCHEMA IF NOT EXISTS "%s"' % sch)

    # Materialise the canonical ORM schema so the chain is reproducible from a
    # clean database. checkfirst=True (default) makes this a no-op on databases
    # that already contain the tables (e.g. prod already stamped past baseline).
    # Note: This migration runs via Alembic (APP_ENV=development or production),
    # never via direct Base.metadata.create_all() calls.
    Base.metadata.create_all(op.get_bind())

    # Residual baseline deltas. Every operation is guarded so it is a safe
    # no-op when the referenced object already exists (e.g. columns created by
    # create_all() above), matching the original "delta" intent.
    if _has_table("internal_messages") and not _has_column(
        "internal_messages", "is_deleted"
    ):
        safe_add_column(op, 
            "internal_messages",
            sa.Column("is_deleted", sa.Boolean(), nullable=True),
        )

    if _has_table("org_units"):
        if not _has_column("org_units", "path"):
            safe_add_column(op, 
                "org_units",
                sa.Column(
                    "path",
                    sa.String(length=500),
                    nullable=True,
                    comment="Materialized path like '/1/12/45/'",
                ),
            )
        if not _has_column("org_units", "depth"):
            safe_add_column(op, 
                "org_units",
                sa.Column(
                    "depth",
                    sa.Integer(),
                    nullable=True,
                    comment="Depth in hierarchy (0 = root)",
                ),
            )
        safe_create_index(op, "ix_org_unit_parent", "org_units", ["parent_id"], unique=False)
        safe_create_index(op, "ix_org_unit_path", "org_units", ["path"], unique=False)

    if _has_table("sales_order_lines"):
        safe_create_index(op, op.f("ix_sales_order_lines_id"), "sales_order_lines", ["id"], unique=False)
        safe_create_index(op, 
            op.f("ix_sales_order_lines_so_id"), "sales_order_lines", ["so_id"], unique=False
        )


def downgrade() -> None:
    if _has_table("sales_order_lines"):
        safe_drop_index(op, op.f("ix_sales_order_lines_so_id"), table_name="sales_order_lines")
        safe_drop_index(op, op.f("ix_sales_order_lines_id"), table_name="sales_order_lines")
    if _has_table("org_units"):
        safe_drop_index(op, "ix_org_unit_path", table_name="org_units")
        safe_drop_index(op, "ix_org_unit_parent", table_name="org_units")
        if _has_column("org_units", "depth"):
            safe_drop_column(op, "org_units", "depth")
        if _has_column("org_units", "path"):
            safe_drop_column(op, "org_units", "path")
    if _has_table("internal_messages") and _has_column("internal_messages", "is_deleted"):
        safe_drop_column(op, "internal_messages", "is_deleted")

    # Drop every ORM table created by the canonical schema in reverse order.
    Base.metadata.drop_all(op.get_bind())
