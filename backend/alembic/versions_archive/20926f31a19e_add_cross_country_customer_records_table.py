"""add_cross_country_customer_records_table

Create cross_country_customer_records table for cross-border customer tracking.

Revision ID: 20926f31a19e
Revises: 20926f31a19d
Create Date: 2026-06-25 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20926f31a19e"
down_revision: Union[str, Sequence[str], None] = "20926f31a19d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    
    # Create normalized cross_country_customer_records table
    if "cross_country_customer_records" not in existing_tables:
        op.create_table(
            "cross_country_customer_records",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("customer_id", sa.BigInteger(), nullable=False),  # user id
            sa.Column("home_country_code", sa.String(length=10), nullable=False),
            sa.Column("operating_country_code", sa.String(length=10), nullable=False),
            sa.Column("currency_used", sa.String(length=10), nullable=False),
            sa.Column("applied_tax_rate", sa.Numeric(precision=5, scale=4), nullable=True),
            sa.Column("available_payment_methods_json", sa.Text(), nullable=True),
            sa.Column("available_logistics_json", sa.Text(), nullable=True),
            sa.Column("session_started_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(
                ["home_country_code"], ["country_configs.code"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["operating_country_code"], ["country_configs.code"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("pk_cross_country_customer_records"),
        )
        
        # Add indexes
        op.create_index(
            "ix_cross_country_customer_records_home_operating",
            "cross_country_customer_records",
            ["home_country_code", "operating_country_code"],
        )
        op.create_index(
            "ix_cross_country_customer_records_customer",
            "cross_country_customer_records",
            ["customer_id", "operating_country_code"],
        )

def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_cross_country_customer_records_home_operating", table_name="cross_country_customer_records")
    op.drop_index("ix_cross_country_customer_records_customer", table_name="cross_country_customer_records")
    
    # Drop table
    op.drop_table("cross_country_customer_records")

