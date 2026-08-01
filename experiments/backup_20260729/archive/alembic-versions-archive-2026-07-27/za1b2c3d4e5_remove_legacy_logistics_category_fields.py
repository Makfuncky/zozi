"""remove_legacy_logistics_category_fields

Revision ID: za1b2c3d4e5
Revises: y3z4a5b6c7d8
Create Date: 2026-04-10 10:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "za1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "y3z4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("logistics_category_pricing_rules", schema=None) as batch_op:
        batch_op.drop_constraint("ck_lp_category_rules_fragile_multiplier_positive", type_="check")
        batch_op.drop_constraint("ck_lp_category_rules_per_kg_nonnegative", type_="check")
        batch_op.drop_column("fragile_multiplier")
        batch_op.drop_column("per_kg_rate_override")


def downgrade() -> None:
    with op.batch_alter_table("logistics_category_pricing_rules", schema=None) as batch_op:
        batch_op.add_column(sa.Column("per_kg_rate_override", sa.Numeric(precision=12, scale=2), nullable=True))
        batch_op.add_column(sa.Column("fragile_multiplier", sa.Numeric(precision=8, scale=4), nullable=True))
        batch_op.create_check_constraint(
            "ck_lp_category_rules_per_kg_nonnegative",
            "per_kg_rate_override IS NULL OR per_kg_rate_override >= 0",
        )
        batch_op.create_check_constraint(
            "ck_lp_category_rules_fragile_multiplier_positive",
            "fragile_multiplier IS NULL OR fragile_multiplier > 0",
        )

