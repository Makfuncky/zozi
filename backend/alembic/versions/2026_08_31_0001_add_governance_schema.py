"""Add governance schema and move admin tables

Revision ID: 20260831_0001
Revises: 20260827_audit_logs_worm_hash
Create Date: 2026-08-31
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260831_0001"
down_revision: Union[str, None] = "20260827_audit_logs_worm_hash"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    # Create governance schema
    op.execute('CREATE SCHEMA IF NOT EXISTS "governance"')

    # Move admin tables from audit to governance schema
    for table_name in [
        "admin_activity_logs",
        "admin_analytics_snapshots",
        "admin_change_audit_logs",
    ]:
        op.execute(
            f'ALTER TABLE IF EXISTS "audit"."{table_name}" SET SCHEMA "governance"'
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    # Move tables back to audit schema
    for table_name in [
        "admin_activity_logs",
        "admin_analytics_snapshots",
        "admin_change_audit_logs",
    ]:
        op.execute(
            f'ALTER TABLE IF EXISTS "governance"."{table_name}" SET SCHEMA "audit"'
        )

    # Drop governance schema
    op.execute('DROP SCHEMA IF EXISTS "governance" CASCADE')
