"""add_incident_model_audit_columns

Adds missing audit columns to ``comms`` incident tables per ARCHITECTURE_STACK.md
Law 23 (every model MUST include created_at, updated_at, country_code, is_deleted):

  - ``incident_war_rooms``  gains created_at, country_code
  - ``incident_threads``    gains country_code
  - ``incident_action_items`` gains country_code
  - ``war_room_templates``  gains updated_at, country_code

Idempotent and skipped on SQLite: dev/test databases are recreated from ORM
metadata which already carries the corrected column definitions.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from migration_helpers import safe_add_column

revision: str = "20260930_0004"
down_revision: Union[str, None] = "20260930_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # incident_war_rooms: add created_at, country_code
    for col_name, col_def in [
        (
            "created_at",
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        ),
        (
            "country_code",
            sa.Column("country_code", sa.String(length=2), nullable=True),
        ),
    ]:
        safe_add_column(op, "incident_war_rooms", col_def, schema="comms")

    # Add index for country_code on incident_war_rooms
    existing_idx = {i["name"] for i in inspector.get_indexes("incident_war_rooms", schema="comms")}
    if "ix_comms_incident_war_rooms_country_code" not in existing_idx:
        op.create_index(
            "ix_comms_incident_war_rooms_country_code",
            "incident_war_rooms",
            ["country_code"],
            schema="comms",
            if_not_exists=True,
        )

    # incident_threads: add country_code
    safe_add_column(
        op,
        "incident_threads",
        sa.Column("country_code", sa.String(length=2), nullable=True),
        schema="comms",
    )
    existing_idx = {i["name"] for i in inspector.get_indexes("incident_threads", schema="comms")}
    if "ix_comms_incident_threads_country_code" not in existing_idx:
        op.create_index(
            "ix_comms_incident_threads_country_code",
            "incident_threads",
            ["country_code"],
            schema="comms",
            if_not_exists=True,
        )

    # incident_action_items: add country_code
    safe_add_column(
        op,
        "incident_action_items",
        sa.Column("country_code", sa.String(length=2), nullable=True),
        schema="comms",
    )
    existing_idx = {i["name"] for i in inspector.get_indexes("incident_action_items", schema="comms")}
    if "ix_comms_incident_action_items_country_code" not in existing_idx:
        op.create_index(
            "ix_comms_incident_action_items_country_code",
            "incident_action_items",
            ["country_code"],
            schema="comms",
            if_not_exists=True,
        )

    # war_room_templates: add updated_at, country_code
    for col_name, col_def in [
        (
            "updated_at",
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        ),
        (
            "country_code",
            sa.Column("country_code", sa.String(length=2), nullable=True),
        ),
    ]:
        safe_add_column(op, "war_room_templates", col_def, schema="comms")

    existing_idx = {i["name"] for i in inspector.get_indexes("war_room_templates", schema="comms")}
    if "ix_comms_war_room_templates_country_code" not in existing_idx:
        op.create_index(
            "ix_comms_war_room_templates_country_code",
            "war_room_templates",
            ["country_code"],
            schema="comms",
            if_not_exists=True,
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Drop indexes first
    for table, idx_name in [
        ("war_room_templates", "ix_comms_war_room_templates_country_code"),
        ("incident_action_items", "ix_comms_incident_action_items_country_code"),
        ("incident_threads", "ix_comms_incident_threads_country_code"),
        ("incident_war_rooms", "ix_comms_incident_war_rooms_country_code"),
    ]:
        existing_idx = {i["name"] for i in inspector.get_indexes(table, schema="comms")}
        if idx_name in existing_idx:
            try:
                op.drop_index(idx_name, table_name=table, schema="comms")
            except Exception:
                pass

    # Drop columns
    for table, col_name in [
        ("war_room_templates", "country_code"),
        ("war_room_templates", "updated_at"),
        ("incident_action_items", "country_code"),
        ("incident_threads", "country_code"),
        ("incident_war_rooms", "country_code"),
        ("incident_war_rooms", "created_at"),
    ]:
        existing = {c["name"] for c in inspector.get_columns(table, schema="comms")}
        if col_name in existing:
            op.drop_column(table, col_name, schema="comms")
