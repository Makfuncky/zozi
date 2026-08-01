"""add_country_category_tax_rates_table

Create normalized country_category_tax_rates table to replace CountryConfig.category_tax_rates_json blob.

Revision ID: 20926f31a19b
Revises: 20926f31a19a
Create Date: 2026-06-25 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20926f31a19b"
down_revision: Union[str, Sequence[str], None] = "20926f31a19a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    
    # Create normalized country_category_tax_rates table
    if "country_category_tax_rates" not in existing_tables:
        op.create_table(
            "country_category_tax_rates",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("category_id", sa.BigInteger(), nullable=False),  # Reference to categories table if exists
            sa.Column("tax_rate", sa.Numeric(precision=5, scale=4), nullable=False),  # Decimal like 0.05 for 5%
            sa.Column("tax_name", sa.String(length=100), nullable=True),  # e.g., "VAT", "GST"
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
            sa.ForeignKeyConstraint(
                ["country_code"], ["country_configs.code"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("pk_country_category_tax_rates"),
            sa.UniqueConstraint(
                "uq_country_category_tax_rates_country_category",
                "country_code", "category_id",
                name="country_category_tax_rates_unique",
            ),
        )
        
        # Add indexes
        op.create_index(
            "ix_country_category_tax_rates_country_category",
            "country_category_tax_rates",
            ["country_code", "category_id"],
        )
        op.create_index(
            "ix_country_category_tax_rates_country",
            "country_category_tax_rates",
            ["country_code"],
        )

def downgrade() -> None:
    # Drop index first
    op.drop_index("ix_country_category_tax_rates_country_category", table_name="country_category_tax_rates")
    op.drop_index("ix_country_category_tax_rates_country", table_name="country_category_tax_rates")
    
    # Drop table
    op.drop_table("country_category_tax_rates")

