"""add_composite_indexes

Revision ID: 20260831_0004
Revises: 20260831_0003
Create Date: 2026-08-31
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import quoted_name

revision: str = "20260831_0004"
down_revision: Union[str, None] = "20260831_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def sql_identifier(name: str):
    return quoted_name(name, False)


COMPOSITE_INDEXES = [
    ("commerce", "products", "ix_products_country_brand", ["country_code", "brand"]),
    ("commerce", "products", "ix_products_country_category", ["country_code", "category_id"]),
    ("commerce", "products", "ix_products_country_price", ["country_code", "price"]),
    ("customer", "customers", "ix_customers_country_email", ["country_code", "email"]),
    ("customer", "addresses", "ix_addresses_country_city", ["country_code", "city"]),
]

PARTIAL_INDEXES = [
    ("commerce", "products", "ix_products_active_country", ["country_code"], "is_active = true"),
    ("customer", "customers", "ix_customers_active_country", ["country_code"], "is_active = true"),
]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return  # SQLite indexes are less critical, skip for dev

    # Create composite indexes
    for schema, table, idx_name, columns in COMPOSITE_INDEXES:
        col_list = ", ".join(columns)
        op.execute(
            f"CREATE INDEX IF NOT EXISTS {idx_name} ON {schema}.{table} ({col_list})"
        )

    # Create partial indexes
    for schema, table, idx_name, columns, where_clause in PARTIAL_INDEXES:
        col_list = ", ".join(columns)
        op.execute(
            f"CREATE INDEX IF NOT EXISTS {idx_name} ON {schema}.{table} ({col_list}) WHERE {where_clause}"
        )


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    # Drop partial indexes (in reverse)
    for schema, table, idx_name, _columns, _where in reversed(PARTIAL_INDEXES):
        op.execute(
            f"DROP INDEX IF EXISTS {schema}.{idx_name}"
        )

    # Drop composite indexes (in reverse)
    for schema, table, idx_name, _columns in reversed(COMPOSITE_INDEXES):
        op.execute(
            f"DROP INDEX IF EXISTS {schema}.{idx_name}"
        )
