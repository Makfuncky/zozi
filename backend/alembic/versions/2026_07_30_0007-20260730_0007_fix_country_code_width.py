"""fix_country_code_width

Revision ID: 20260730_0007
Revises: 20260730_0005
Create Date: 2026-07-30

"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260730_0007"
down_revision: Union[str, None] = "20260730_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    op.execute("ALTER TABLE country.country_configs ALTER COLUMN code TYPE VARCHAR(3)")
    op.execute("ALTER TABLE country.country_communications ALTER COLUMN country_code TYPE VARCHAR(3)")
    op.execute("ALTER TABLE country.country_gateway_credentials ALTER COLUMN country_code TYPE VARCHAR(3)")
    op.execute("ALTER TABLE country.tax_rules ALTER COLUMN country_code TYPE VARCHAR(3)")
    op.execute("ALTER TABLE finance.payout_rules ALTER COLUMN country_code TYPE VARCHAR(3)")


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    op.execute("ALTER TABLE country.country_configs ALTER COLUMN code TYPE VARCHAR(10)")
    op.execute("ALTER TABLE country.country_communications ALTER COLUMN country_code TYPE VARCHAR(10)")
    op.execute("ALTER TABLE country.country_gateway_credentials ALTER COLUMN country_code TYPE VARCHAR(10)")
    op.execute("ALTER TABLE country.tax_rules ALTER COLUMN country_code TYPE VARCHAR(10)")
    op.execute("ALTER TABLE finance.payout_rules ALTER COLUMN country_code TYPE VARCHAR(10)")