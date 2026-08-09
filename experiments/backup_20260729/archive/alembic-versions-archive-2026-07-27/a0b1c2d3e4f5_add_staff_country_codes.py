"""add_staff_country_codes_column

Revision ID: a0b1c2d3e4f5
Revises: s1t2u3v4w5x7
Create Date: 2026-06-22 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a0b1c2d3e4f5"
down_revision: Union[str, None] = "s1t2u3v4w5x7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("staff_country_codes", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "staff_country_codes")

