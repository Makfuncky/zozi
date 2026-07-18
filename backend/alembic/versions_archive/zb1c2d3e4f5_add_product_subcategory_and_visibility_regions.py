"""add_product_subcategory_and_visibility_regions

Revision ID: zb1c2d3e4f5
Revises: za1b2c3d4e5
Create Date: 2026-04-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "zb1c2d3e4f5"
down_revision: Union[str, Sequence[str], None] = "za1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.add_column(sa.Column("subcategory", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("visibility_regions", sa.Text(), nullable=True))
        batch_op.create_index("ix_products_subcategory", ["subcategory"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_index("ix_products_subcategory")
        batch_op.drop_column("visibility_regions")
        batch_op.drop_column("subcategory")

