"""add_country_config_versions_table

Create country_config_versions table for draft-to-publish versioning.

Revision ID: 20926f31a19f
Revises: 20926f31a19e
Create Date: 2026-06-25 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20926f31a19f"
down_revision: Union[str, Sequence[str], None] = "20926f31a19e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    
    # Create country_config_versions table
    if "country_config_versions" not in existing_tables:
        op.create_table(
            "country_config_versions",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("version_number", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("config_snapshot_json", sa.Text(), nullable=False),  # JSON snapshot of entire country config
            sa.Column("created_by", sa.BigInteger(), nullable=True),
            sa.Column("approved_by", sa.BigInteger(), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("published_at", sa.DateTime(), nullable=True),
            sa.Column("rolled_back_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["country_code"], ["country_configs.code"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["created_by"], ["users.id"],
                ondelete="SET NULL",
            ),
            sa.ForeignKeyConstraint(
                ["approved_by"], ["users.id"],
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("pk_country_config_versions"),
        )
        
        # Add indexes
        op.create_index(
            "ix_country_config_versions_country_status",
            "country_config_versions",
            ["country_code", "status"],
        )
        op.create_index(
            "ix_country_config_versions_country_version",
            "country_config_versions",
            ["country_code", "version_number"],
        )

def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_country_config_versions_country_status", table_name="country_config_versions")
    op.drop_index("ix_country_config_versions_country_version", table_name="country_config_versions")
    
    # Drop table
    op.drop_table("country_config_versions")

