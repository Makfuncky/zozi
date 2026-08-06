"""add_country_communications_table

Create normalized country_communications table for internal communications.

Revision ID: 20926f31a19d
Revises: 20926f31a19c
Create Date: 2026-06-25 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20926f31a19d"
down_revision: Union[str, Sequence[str], None] = "20926f31a19c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    
    # Create normalized country_communications table
    if "country_communications" not in existing_tables:
        op.create_table(
            "country_communications",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("sender_id", sa.BigInteger(), nullable=True),  # user who sent
            sa.Column("recipient_role", sa.String(length=30), nullable=False),  # admin, country_head, country_manager, etc.
            sa.Column("recipient_user_id", sa.BigInteger(), nullable=True),  # specific user if targeting individual
            sa.Column("category", sa.String(length=50), nullable=False),  # operational, financial, escalation
            sa.Column("priority", sa.String(length=20), nullable=False, server_default="normal"),
            sa.Column("subject", sa.String(length=200), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("related_entity_type", sa.String(length=50), nullable=True),  # order, supplier, ticket, payout
            sa.Column("related_entity_id", sa.BigInteger(), nullable=True),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("read_at", sa.DateTime(), nullable=True),
            sa.Column("attachments_json", sa.Text(), nullable=True),  # JSON array of attachment metadata
            sa.ForeignKeyConstraint(
                ["country_code"], ["country_configs.code"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("pk_country_communications"),
        )
        
        # Add indexes
        op.create_index(
            "ix_country_communications_country_status",
            "country_communications",
            ["country_code", "is_read"],
        )
        op.create_index(
            "ix_country_communications_recipient",
            "country_communications",
            ["recipient_role", "recipient_user_id"],
        )

def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_country_communications_country_status", table_name="country_communications")
    op.drop_index("ix_country_communications_recipient", table_name="country_communications")
    
    # Drop table
    op.drop_table("country_communications")

