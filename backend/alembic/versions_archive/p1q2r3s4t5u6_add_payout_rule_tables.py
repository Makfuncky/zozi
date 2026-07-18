"""add_payout_rule_tables

Revision ID: p1q2r3s4t5u6
Revises: a0b1c2d3e4f5
Create Date: 2026-06-22 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p1q2r3s4t5u6"
down_revision: Union[str, None] = "a0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payout_rule_categories",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("country_code", sa.String(10), nullable=False, index=True),
        sa.Column("category_slug", sa.String(120), nullable=False),
        sa.Column("payout_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("min_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("max_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("country_code", "category_slug", name="uq_payout_rule_cat"),
        sa.CheckConstraint("payout_rate >= 0 AND payout_rate <= 1", name="ck_payout_rule_cat_rate"),
    )
    op.create_table(
        "payout_rule_products",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("country_code", sa.String(10), nullable=False, index=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("payout_rate", sa.Numeric(5, 4), nullable=False),
        sa.Column("min_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("max_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("country_code", "product_id", name="uq_payout_rule_product"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )


def downgrade() -> None:
    op.drop_table("payout_rule_products")
    op.drop_table("payout_rule_categories")

