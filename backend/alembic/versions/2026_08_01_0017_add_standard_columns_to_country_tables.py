"""add_standard_columns_to_country_tables

Constitution §2.9 (Phase 5): every country-scoped / country-entity table
must carry the full mandatory column set — ``uuid`` (stable public
identifier), ``version`` (optimistic concurrency), plus the audit and
soft-delete columns already present on ``CountryTax``.

Tables that already have ``uuid`` + ``version`` (via model declaration):
  - CountryTax  ✅ (migration 0008)

Tables that need ``uuid`` + ``version`` added:
  - country.country_configs
  - country.country_basics
  - country.country_economics
  - country.country_legal

Revision ID: 20260801_0017
Revises: 20260801_0016
Create Date: 2026-08-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migration_helpers import safe_add_column


revision: str = "20260801_0017"
down_revision: Union[str, None] = "20260801_0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_COUNTRY_TABLES = [
    ("country", "country_configs"),
    ("country", "country_basics"),
    ("country", "country_economics"),
    ("country", "country_legal"),
]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    for schema, table in _COUNTRY_TABLES:
        fqn = f'"{schema}"."{table}"'
        safe_add_column(op, table,
                        sa.Column("uuid", sa.String(36), nullable=True, unique=True, index=True),
                        schema=schema)
        safe_add_column(op, table,
                        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
                        schema=schema)


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    for schema, table in reversed(_COUNTRY_TABLES):
        fqn = f'"{schema}"."{table}"'
        with op.batch_alter_table(table, schema=schema) as batch:
            batch.drop_column("version")
            batch.drop_column("uuid")
