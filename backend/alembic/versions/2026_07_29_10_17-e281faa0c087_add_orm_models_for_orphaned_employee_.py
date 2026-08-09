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

# revision identifiers, used by Alembic.
revision: str = "e281faa0c087"
down_revision: Union[str, None] = "87146598d2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_exists(conn, table_name: str, index_name: str) -> bool:
    """Check if an index already exists in SQLite."""
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=:name AND tbl_name=:tbl"),
        {"name": index_name, "tbl": table_name},
    )
    return result.scalar() > 0


def _fk_exists(conn, table_name: str, from_col: str, to_table: str, to_col: str) -> bool:
    """Check if a FK already exists on a table in SQLite."""
    fks = conn.execute(sa.text(f"PRAGMA foreign_key_list({table_name})")).fetchall()
    for fk in fks:
        # fk[3] = from_column, fk[2] = to_table, fk[4] = to_col
        if fk[3] == from_col and fk[2] == to_table and fk[4] == to_col:
            return True
    return False


def upgrade() -> None:
    bind = op.get_bind()

    # ── employee_active_tasks ────────────────────────────────────────
    if not _index_exists(bind, "employee_active_tasks", "ix_employee_active_tasks_employee_id"):
        with op.batch_alter_table("employee_active_tasks") as batch_op:
            batch_op.create_index(
                "ix_employee_active_tasks_employee_id",
                ["employee_id"],
                unique=False,
            )

    # ── employee_audit_timeline ──────────────────────────────────────
    if not _index_exists(bind, "employee_audit_timeline", "ix_employee_audit_timeline_employee_id"):
        with op.batch_alter_table("employee_audit_timeline") as batch_op:
            batch_op.create_index(
                "ix_employee_audit_timeline_employee_id",
                ["employee_id"],
                unique=False,
            )

    # Align FK: ensure actor_id has SET NULL on delete
    if not _fk_exists(bind, "employee_audit_timeline", "actor_id", "users", "id"):
        with op.batch_alter_table("employee_audit_timeline") as batch_op:
            batch_op.create_foreign_key(
                "fk_audit_timeline_actor",
                "users",
                ["actor_id"],
                ["id"],
                ondelete="SET NULL",
            )

    # ── employee_risk_scores ─────────────────────────────────────────
    if not _index_exists(bind, "employee_risk_scores", "ix_employee_risk_scores_employee_id"):
        with op.batch_alter_table("employee_risk_scores") as batch_op:
            batch_op.create_index(
                "ix_employee_risk_scores_employee_id",
                ["employee_id"],
                unique=False,
            )


def downgrade() -> None:
    # ── employee_risk_scores ─────────────────────────────────────────
    bind = op.get_bind()
    if _index_exists(bind, "employee_risk_scores", "ix_employee_risk_scores_employee_id"):
        with op.batch_alter_table("employee_risk_scores") as batch_op:
            batch_op.drop_index("ix_employee_risk_scores_employee_id")

    # ── employee_audit_timeline ──────────────────────────────────────
    if _index_exists(bind, "employee_audit_timeline", "ix_employee_audit_timeline_employee_id"):
        with op.batch_alter_table("employee_audit_timeline") as batch_op:
            batch_op.drop_index("ix_employee_audit_timeline_employee_id")

    # ── employee_active_tasks ────────────────────────────────────────
    if _index_exists(bind, "employee_active_tasks", "ix_employee_active_tasks_employee_id"):
        with op.batch_alter_table("employee_active_tasks") as batch_op:
            batch_op.drop_index("ix_employee_active_tasks_employee_id")
