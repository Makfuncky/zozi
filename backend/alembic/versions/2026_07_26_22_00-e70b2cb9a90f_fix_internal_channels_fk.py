"""fix_internal_channels_fk

Revision ID: e70b2cb9a90f
Revises: 837e1e29bd49
Create Date: 2026-07-26 22:00:00.000000+00:00

Adds the missing FK constraint from ``internal_channels.created_by`` to
``users.id``.  The constraint was omitted in the original
``c9e8f7d6a5b4`` migration that created the table, even though the ORM
model defines it.

SQLite cannot ``ALTER TABLE ADD CONSTRAINT``, so this migration uses
Alembic's batch mode (copy-and-move strategy).  On PostgreSQL the batch
mode transparently emits ``ALTER TABLE ... ADD CONSTRAINT`` instead.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e70b2cb9a90f"
down_revision: Union[str, None] = "837e1e29bd49"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("internal_channels") as batch_op:
        batch_op.create_foreign_key(
            "fk_internal_channels_created_by",
            "users",
            ["created_by"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("internal_channels") as batch_op:
        batch_op.drop_constraint(
            "fk_internal_channels_created_by", type_="foreignkey"
        )
