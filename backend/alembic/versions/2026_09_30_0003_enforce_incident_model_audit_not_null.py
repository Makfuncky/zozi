"""enforce_incident_model_audit_not_null

Alters incident ``country_code`` and ``created_at`` columns to ``nullable=False``
per ARCHITECTURE_STACK.md Law 23 (every model MUST include created_at,
updated_at, country_code, is_deleted with proper nullability).

Resolves the remaining benchmark mismatches in FILE-005 where the ORM was
corrected to ``nullable=False`` but the database still allows NULLs:

  - ``comms.incident_war_rooms.country_code``   → nullable=False
  - ``comms.incident_threads.country_code``     → nullable=False
  - ``comms.incident_threads.created_at``       → nullable=False
  - ``comms.incident_action_items.country_code`` → nullable=False
  - ``comms.incident_action_items.created_at``   → nullable=False
  - ``comms.war_room_templates.country_code``    → nullable=False

Idempotent. Skipped on SQLite: dev/test databases are recreated from ORM
metadata which already carries the corrected column definitions.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260930_0003"
down_revision: Union[str, None] = "20260930_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Map of (table, column) pairs to enforce NOT NULL
    not_null_columns = [
        ("incident_war_rooms", "country_code"),
        ("incident_threads", "country_code"),
        ("incident_threads", "created_at"),
        ("incident_action_items", "country_code"),
        ("incident_action_items", "created_at"),
        ("war_room_templates", "country_code"),
    ]

    for table_name, col_name in not_null_columns:
        existing_cols = {
            c["name"] for c in inspector.get_columns(table_name, schema="comms")
        }
        if col_name not in existing_cols:
            continue

        col_info = next(
            c for c in inspector.get_columns(table_name, schema="comms")
            if c["name"] == col_name
        )
        if col_info.get("nullable", True):
            with op.batch_alter_table(table_name, schema="comms") as batch_op:
                batch_op.alter_column(
                    col_name,
                    existing_type=sa.String(length=2) if "country_code" in col_name else sa.DateTime(),
                    nullable=False,
                )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    nullable_columns = [
        ("incident_war_rooms", "country_code"),
        ("incident_threads", "country_code"),
        ("incident_threads", "created_at"),
        ("incident_action_items", "country_code"),
        ("incident_action_items", "created_at"),
        ("war_room_templates", "country_code"),
    ]

    for table_name, col_name in nullable_columns:
        existing_cols = {
            c["name"] for c in inspector.get_columns(table_name, schema="comms")
        }
        if col_name not in existing_cols:
            continue

        with op.batch_alter_table(table_name, schema="comms") as batch_op:
            batch_op.alter_column(
                col_name,
                existing_type=sa.String(length=2) if "country_code" in col_name else sa.DateTime(),
                nullable=True,
            )
