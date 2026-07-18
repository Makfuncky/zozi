"""add_product_badge_fields

Revision ID: b1c2d3e4f5a6
Revises: a3b4c5d6e7f8
Create Date: 2026-03-24 12:00:00.000000

Adds:
  - products.is_hot    (Boolean nullable) — admin-pinned HOT badge
  - products.is_featured (Boolean nullable) — admin-pinned FEATURED badge
  - products.is_new    (Boolean nullable) — supplier/admin-pinned NEW badge
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = ("a3b4c5d6e7f8", "cabbef94c669")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {c["name"] for c in inspector.get_columns("products")}

    with op.batch_alter_table("products", schema=None) as batch_op:
        if "is_hot" not in existing_cols:
            batch_op.add_column(sa.Column("is_hot", sa.Boolean(), nullable=True))
        if "is_featured" not in existing_cols:
            batch_op.add_column(sa.Column("is_featured", sa.Boolean(), nullable=True))
        if "is_new" not in existing_cols:
            batch_op.add_column(sa.Column("is_new", sa.Boolean(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.drop_column("is_new")
        batch_op.drop_column("is_featured")
        batch_op.drop_column("is_hot")

