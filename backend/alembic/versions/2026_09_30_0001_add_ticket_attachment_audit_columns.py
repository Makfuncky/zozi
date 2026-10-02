"""add_ticket_attachment_audit_columns

Adds missing audit columns to ``comms.ticket_attachments``:
  - ``updated_at``  DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
  - ``server_default=func.now()`` on existing ``created_at`` column

TicketAttachment is the only table in the comms domain missing these audit
columns per audit findings in FILE-db-communication-models (findings 1 & 2).

Skipped on SQLite: dev/test databases are recreated from ORM metadata which
already carries the corrected column definitions.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migration_helpers import safe_add_column

revision: str = "20260930_0001"
down_revision: Union[str, None] = "20260929_0745"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {
        c["name"] for c in inspector.get_columns("ticket_attachments", schema="comms")
    }

    # 1. Add updated_at if missing
    if "updated_at" not in existing_cols:
        safe_add_column(
            op,
            "ticket_attachments",
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            ),
            schema="comms",
        )

    # 2. Ensure created_at has server_default=func.now() (idempotent)
    created_at_cols = [
        c for c in inspector.get_columns("ticket_attachments", schema="comms")
        if c["name"] == "created_at"
    ]
    if created_at_cols:
        col = created_at_cols[0]
        has_server_default = col.get("default") is not None and hasattr(
            col.get("default"), "is_scalar"
        ) is False
        if not has_server_default:
            with op.batch_alter_table("ticket_attachments", schema="comms") as batch_op:
                batch_op.alter_column(
                    "created_at",
                    existing_type=sa.DateTime(),
                    server_default=sa.func.now(),
                    existing_nullable=True,
                )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {
        c["name"] for c in inspector.get_columns("ticket_attachments", schema="comms")
    }

    # Remove server_default from created_at
    created_at_cols = [
        c for c in inspector.get_columns("ticket_attachments", schema="comms")
        if c["name"] == "created_at"
    ]
    if created_at_cols:
        with op.batch_alter_table("ticket_attachments", schema="comms") as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(),
                server_default=None,
                existing_nullable=True,
            )

    # Drop updated_at if present
    if "updated_at" in existing_cols:
        with op.batch_alter_table("ticket_attachments", schema="comms") as batch_op:
            batch_op.drop_column("updated_at")
