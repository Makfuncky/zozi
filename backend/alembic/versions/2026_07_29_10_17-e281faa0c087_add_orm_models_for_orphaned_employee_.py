"""add_orm_models_for_orphaned_employee_tables

Revision ID: e281faa0c087
Revises: 87146598d2c3
Create Date: 2026-07-29 10:17:22.207462+00:00

This migration aligns the ORM models with 3 orphaned tables that were
created by _GAP_DDL in tests/conftest.py but never had ORM models.

Uses SQLite-compatible batch_alter_table for all operations.
Idempotent: skips creating indexes/constraints that already exist.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

# revision identifiers, used by Alembic.
revision: str = "e281faa0c087"
down_revision: Union[str, None] = "87146598d2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_offline_connection(conn) -> bool:
    """Return True when running in alembic --sql offline mode."""
    if conn is None:
        return True
    try:
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


def _index_exists(conn, table_name: str, index_name: str, schema: str | None = None) -> bool:
    """Return True when ``index_name`` already exists on ``table_name``."""
    if conn is None:
        raise RuntimeError("Cannot check index existence offline (--sql)")
    inspector = sa_inspect(conn)
    existing = {i["name"] for i in inspector.get_indexes(table_name, schema=schema)}
    return index_name in existing


def _fk_exists(conn, table_name: str, from_col: str, to_table: str, to_col: str, schema: str | None = None) -> bool:
    """Return True when a matching FK already exists on ``table_name``."""
    if conn is None:
        raise RuntimeError("Cannot check FK existence offline (--sql)")
    inspector = sa_inspect(conn)
    for fk in inspector.get_foreign_keys(table_name, schema=schema):
        if from_col in fk["constrained_columns"] and to_table == fk["referred_table"] and to_col in fk["referred_columns"]:
            return True
    return False


def upgrade() -> None:
    bind = op.get_bind()
    offline = _is_offline_connection(bind)

    # ── employee_active_tasks ────────────────────────────────────────
    if offline or not _index_exists(bind, "employee_active_tasks", "ix_employee_active_tasks_employee_id"):
        with op.batch_alter_table("employee_active_tasks") as batch_op:
            batch_op.create_index(
                "ix_employee_active_tasks_employee_id",
                ["employee_id"],
                unique=False,
            )

    # ── employee_audit_timeline ──────────────────────────────────────
    if offline or not _index_exists(bind, "employee_audit_timeline", "ix_employee_audit_timeline_employee_id"):
        with op.batch_alter_table("employee_audit_timeline") as batch_op:
            batch_op.create_index(
                "ix_employee_audit_timeline_employee_id",
                ["employee_id"],
                unique=False,
            )

    if offline or not _fk_exists(bind, "employee_audit_timeline", "actor_id", "users", "id"):
        with op.batch_alter_table("employee_audit_timeline") as batch_op:
            batch_op.create_foreign_key(
                "fk_audit_timeline_actor",
                "users",
                ["actor_id"],
                ["id"],
                ondelete="SET NULL",
            )

    # ── employee_risk_scores ─────────────────────────────────────────
    if offline or not _index_exists(bind, "employee_risk_scores", "ix_employee_risk_scores_employee_id"):
        with op.batch_alter_table("employee_risk_scores") as batch_op:
            batch_op.create_index(
                "ix_employee_risk_scores_employee_id",
                ["employee_id"],
                unique=False,
            )


def downgrade() -> None:
    bind = op.get_bind()
    offline = _is_offline_connection(bind)

    # ── employee_risk_scores ─────────────────────────────────────────
    if offline or _index_exists(bind, "employee_risk_scores", "ix_employee_risk_scores_employee_id"):
        with op.batch_alter_table("employee_risk_scores") as batch_op:
            batch_op.drop_index("ix_employee_risk_scores_employee_id")

    # ── employee_audit_timeline ──────────────────────────────────────
    if offline or _index_exists(bind, "employee_audit_timeline", "ix_employee_audit_timeline_employee_id"):
        with op.batch_alter_table("employee_audit_timeline") as batch_op:
            batch_op.drop_index("ix_employee_audit_timeline_employee_id")

    # ── employee_active_tasks ────────────────────────────────────────
    if offline or _index_exists(bind, "employee_active_tasks", "ix_employee_active_tasks_employee_id"):
        with op.batch_alter_table("employee_active_tasks") as batch_op:
            batch_op.drop_index("ix_employee_active_tasks_employee_id")
