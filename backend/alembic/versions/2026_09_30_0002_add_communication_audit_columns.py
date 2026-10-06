"""add_communication_model_audit_columns

Adds missing ``country_code`` column and composite index to ``comms.announcements``
and ``comms.help_categories`` per ARCHITECTURE_STACK.md Law 23.

Findings resolved:
  TF-008: Announcement has no country_code
  TF-009: HelpCategory has no country_code

Skipped on SQLite: dev/test databases are recreated from ORM metadata which
already carries the corrected column definitions.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import NoInspectionAvailable

revision: str = "20260930_0002"
down_revision: Union[str, None] = "20260930_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_offline(conn) -> bool:
    if conn is None:
        return True
    try:
        sa_inspect(conn)
        return False
    except (NoInspectionAvailable, Exception):
        return True


def upgrade() -> None:
    bind = op.get_bind()
    if not _is_offline(bind) and bind.dialect.name == "sqlite":
        return

    for table_name, idx_name in (
        ("announcements", "ix_announcements_country_created"),
        ("help_categories", "ix_help_categories_country_created"),
    ):
        with op.batch_alter_table(table_name, schema="comms") as batch_op:
            batch_op.add_column(
                sa.Column("country_code", sa.String(length=2), nullable=True)
            )
            batch_op.create_index(
                idx_name,
                ["country_code", "created_at"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    if not _is_offline(bind) and bind.dialect.name == "sqlite":
        return

    for table_name, idx_name in (
        ("announcements", "ix_announcements_country_created"),
        ("help_categories", "ix_help_categories_country_created"),
    ):
        with op.batch_alter_table(table_name, schema="comms") as batch_op:
            batch_op.drop_index(idx_name)
            batch_op.drop_column("country_code")
