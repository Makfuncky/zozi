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

revision: str = "20260930_0002"
down_revision: Union[str, None] = "20260930_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table_name, idx_name in (
        ("announcements", "ix_announcements_country_created"),
        ("help_categories", "ix_help_categories_country_created"),
    ):
        existing_cols = {
            c["name"] for c in inspector.get_columns(table_name, schema="comms")
        }

        if "country_code" not in existing_cols:
            with op.batch_alter_table(table_name, schema="comms") as batch_op:
                batch_op.add_column(
                    sa.Column("country_code", sa.String(length=2), nullable=True)
                )

        existing_idxs = {i["name"] for i in inspector.get_indexes(table_name, schema="comms")}
        if idx_name not in existing_idxs:
            with op.batch_alter_table(table_name, schema="comms") as batch_op:
                batch_op.create_index(
                    idx_name,
                    ["country_code", "created_at"],
                )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    for table_name, idx_name in (
        ("announcements", "ix_announcements_country_created"),
        ("help_categories", "ix_help_categories_country_created"),
    ):
        inspector = sa.inspect(bind)
        existing_idxs = {i["name"] for i in inspector.get_indexes(table_name, schema="comms")}
        if idx_name in existing_idxs:
            with op.batch_alter_table(table_name, schema="comms") as batch_op:
                batch_op.drop_index(idx_name)

        existing_cols = {
            c["name"] for c in inspector.get_columns(table_name, schema="comms")
        }
        if "country_code" in existing_cols:
            with op.batch_alter_table(table_name, schema="comms") as batch_op:
                batch_op.drop_column("country_code")
