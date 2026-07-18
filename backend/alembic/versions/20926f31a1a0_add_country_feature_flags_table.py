"""add_country_feature_flags_table

Create country_feature_flags table for per-country feature toggles.

Revision ID: 20926f31a1a0
Revises: 20926f31a19f
Create Date: 2026-06-25 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20926f31a1a0"
down_revision: Union[str, Sequence[str], None] = "20926f31a19f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    
    # Create country_feature_flags table
    if "country_feature_flags" not in existing_tables:
        op.create_table(
            "country_feature_flags",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("feature_key", sa.String(length=100), nullable=False),
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("rollout_percentage", sa.Integer(), nullable=True),  # for gradual rollouts
            sa.Column("rollout_audience", sa.String(length=500), nullable=True),  # targeting rules
            sa.Column("notes", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(
                ["country_code"], ["country_configs.code"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("pk_country_feature_flags"),
            sa.UniqueConstraint(
                "uq_country_feature_flags_country_feature",
                "country_code", "feature_key",
                name="uq_country_feature_flags_country_feature",
            ),
        )
        
        # Add indexes
        op.create_index(
            "ix_country_feature_flags_country_feature",
            "country_feature_flags",
            ["country_code", "feature_key"],
        )
        op.create_index(
            "ix_country_feature_flags_is_enabled",
            "country_feature_flags",
            ["is_enabled"],
        )

def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_country_feature_flags_country_feature", table_name="country_feature_flags")
    op.drop_index("ix_country_feature_flags_is_enabled", table_name="country_feature_flags")
    
    # Drop table
    op.drop_table("country_feature_flags")

