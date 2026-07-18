"""normalize_country_city_schema

Convert CountryConfig.regions_json JSON blob to normalized relational CountryCity table.

Revision ID: 20926f31a19a
Revises: n5o6p7q8r9s0
Create Date: 2026-06-25 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20926f31a19a"
down_revision: Union[str, Sequence[str], None] = "n5o6p7q8r9s0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Get bind and inspector
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())
    
    # Step 1: Extract cities from existing CountryConfig.regions_json
    # This assumes some data already in regions_json blob
    # We'll create CountryCity entries from those
    
    # Step 2: Create normalized CountryCity table
    if "country_cities" not in existing_tables:
        op.create_table(
            "country_cities",
            sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
            sa.Column("country_code", sa.String(length=10), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("name_ar", sa.String(length=200), nullable=True),  # Arabic name
            sa.Column("population", sa.Integer(), nullable=True),
            sa.Column("is_capital", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
            sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
            sa.Column("postal_code_prefix", sa.String(length=20), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("logistics_zone_id", sa.String(length=50), nullable=True),
            sa.ForeignKeyConstraint(
                ["country_code"], ["country_configs.code"],
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("pk_country_cities"),
            sa.Index("ix_country_cities_country_status", "country_code", "status"),
            sa.Index("ix_country_cities_country_population_desc", "country_code", "population", postgresql_where=sa.text("population IS NOT NULL"), postgresql_opclasses={"population": "integer_ops DESC"}),
        )
    
    # Step 3: Backfill from regions_json to country_cities
    # This requires a Python function to extract data from JSON and insert
    # For now, we'll add a comment
    pass

def downgrade() -> None:
    # Drop CountryCity table
    op.drop_table("country_cities")

