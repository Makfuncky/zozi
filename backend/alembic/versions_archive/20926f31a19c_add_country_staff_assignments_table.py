"""add_country_staff_assignments_table

Create normalized country_staff_assignments table for row-level security (RLS).

Revision ID: 20926f31a19c
Revises: 20926f31a19b
Create Date: 2026-06-25 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20926f31a19c"
down_revision: Union[str, Sequence[str], None] = "20926f31a19b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    
    # Create normalized country_staff_assignments table
    if "country_staff_assignments" not in existing_tables:
        op.create_table(
            "country_staff_assignments",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("user_id", sa.BigInteger(), nullable=False),  # Reference to users table
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("role", sa.String(length=50), nullable=False),  # country_head, country_manager, etc.
            sa.Column("assigned_by", sa.BigInteger(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),  # active, inactive
            sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["country_code"], ["country_configs.code"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("pk_country_staff_assignments"),
            sa.UniqueConstraint(
                "uq_country_staff_assignments_user_country_role",
                "user_id", "country_code", "role",
                name="uq_country_staff_assignments_user_country_role",
            ),
        )
        
        # Add indexes
        op.create_index(
            "ix_country_staff_assignments_user_country",
            "country_staff_assignments",
            ["user_id", "country_code", "status"],
        )
        op.create_index(
            "ix_country_staff_assignments_country_role",
            "country_staff_assignments",
            ["country_code", "role"],
        )

def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_country_staff_assignments_user_country", table_name="country_staff_assignments")
    op.drop_index("ix_country_staff_assignments_country_role", table_name="country_staff_assignments")
    
    # Drop table
    op.drop_table("country_staff_assignments")

