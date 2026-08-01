"""create_canonical_platform_tables

Revision ID: 20260731_0010
Revises: 20260730_0009
Create Date: 2026-07-31

Creates DB29 canonical tables:
- commission_rules (commerce schema)
- feature_flags (configuration schema)
- worm_audit (audit schema)
"""
import os
import sys
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(_project_root, "alembic"))
sys.path.insert(0, _project_root)

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from migration_helpers import safe_create_table, safe_drop_table, safe_create_index, safe_drop_index

revision: str = "20260731_0010"
down_revision: Union[str, None] = "20260730_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"

    if is_sqlite:
        schema = None
    else:
        schema = "commerce"

    safe_create_table(op, 
        "commission_rules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("rule_name", sa.String(255), nullable=False, unique=True),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("tier", sa.String(20), nullable=True),
        sa.Column("rate_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("country_code", sa.String(10), nullable=True, index=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        schema=schema,
    )

    if is_sqlite:
        schema = None
    else:
        schema = "configuration"

    safe_create_table(op, 
        "feature_flags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("flag_key", sa.String(100), nullable=False, unique=True),
        sa.Column("flag_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("enabled_for", sa.JSON(), nullable=True),
        sa.Column("disabled_for", sa.JSON(), nullable=True),
        sa.Column("rollout_percentage", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("country_code", sa.String(10), nullable=True, index=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        schema=schema,
    )
    safe_create_index(op, "ix_feature_flags_key_active", "feature_flags", ["flag_key", "is_active"], schema=schema)

    if is_sqlite:
        schema = None
    else:
        schema = "audit"

    safe_create_table(op, 
        "worm_audit",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(100), nullable=False, index=True),
        sa.Column("entity_id", sa.String(100), nullable=False, index=True),
        sa.Column("action", sa.String(50), nullable=False, index=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("actor_type", sa.String(50), nullable=True),
        sa.Column("country_code", sa.String(10), nullable=True, index=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"), index=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("signature", sa.String(255), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("previous_state_hash", sa.String(255), nullable=True),
        sa.Column("new_state_hash", sa.String(255), nullable=True),
        schema=schema,
    )
    safe_create_index(op, "ix_worm_audit_entity_action", "worm_audit", ["entity_type", "action"], schema=schema)
    safe_create_index(op, "ix_worm_audit_timestamp", "worm_audit", ["timestamp"], schema=schema)


def downgrade() -> None:
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"

    if is_sqlite:
        schema = None
    else:
        schema = "audit"

    safe_drop_table(op, "worm_audit", schema=schema)

    if is_sqlite:
        schema = None
    else:
        schema = "configuration"

    safe_drop_index(op, "ix_feature_flags_key_active", table_name="feature_flags", schema=schema)
    safe_drop_table(op, "feature_flags", schema=schema)

    if is_sqlite:
        schema = None
    else:
        schema = "commerce"

    safe_drop_table(op, "commission_rules", schema=schema)
