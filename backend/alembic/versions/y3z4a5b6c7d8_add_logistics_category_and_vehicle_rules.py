"""add_logistics_category_and_vehicle_rules

Revision ID: y3z4a5b6c7d8
Revises: x2y3z4a5b6c7
Create Date: 2026-04-08 16:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "y3z4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "x2y3z4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "logistics_category_pricing_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), sa.ForeignKey("logistics_partners.id"), nullable=False),
        sa.Column("service_area_id", sa.Integer(), sa.ForeignKey("logistics_partner_service_areas.id"), nullable=True),
        sa.Column("category_name", sa.String(length=120), nullable=False),
        sa.Column("flat_fee_override", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("per_kg_rate_override", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("fragile_multiplier", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("special_handling_fee", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("approval_status", sa.String(length=30), nullable=False),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("flat_fee_override IS NULL OR flat_fee_override >= 0", name="ck_lp_category_rules_flat_fee_nonnegative"),
        sa.CheckConstraint("per_kg_rate_override IS NULL OR per_kg_rate_override >= 0", name="ck_lp_category_rules_per_kg_nonnegative"),
        sa.CheckConstraint("fragile_multiplier IS NULL OR fragile_multiplier > 0", name="ck_lp_category_rules_fragile_multiplier_positive"),
        sa.CheckConstraint("special_handling_fee IS NULL OR special_handling_fee >= 0", name="ck_lp_category_rules_special_handling_nonnegative"),
    )
    op.create_index("ix_logistics_category_pricing_rules_id", "logistics_category_pricing_rules", ["id"], unique=False)
    op.create_index("ix_lp_category_rules_partner_status", "logistics_category_pricing_rules", ["partner_id", "approval_status"], unique=False)
    op.create_index("ix_lp_category_rules_service_area", "logistics_category_pricing_rules", ["service_area_id", "approval_status"], unique=False)
    op.create_index("ix_lp_category_rules_category", "logistics_category_pricing_rules", ["category_name", "approval_status"], unique=False)

    op.create_table(
        "logistics_vehicle_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("partner_id", sa.Integer(), sa.ForeignKey("logistics_partners.id"), nullable=False),
        sa.Column("service_area_id", sa.Integer(), sa.ForeignKey("logistics_partner_service_areas.id"), nullable=True),
        sa.Column("route_scope", sa.String(length=20), nullable=False),
        sa.Column("vehicle_type", sa.String(length=50), nullable=False),
        sa.Column("max_weight_kg", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("max_volume_cm3", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("cost_multiplier", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column("priority_rank", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("approval_status", sa.String(length=30), nullable=False),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("max_weight_kg IS NULL OR max_weight_kg >= 0", name="ck_lp_vehicle_rules_max_weight_nonnegative"),
        sa.CheckConstraint("max_volume_cm3 IS NULL OR max_volume_cm3 >= 0", name="ck_lp_vehicle_rules_max_volume_nonnegative"),
        sa.CheckConstraint("cost_multiplier > 0", name="ck_lp_vehicle_rules_cost_multiplier_positive"),
    )
    op.create_index("ix_logistics_vehicle_rules_id", "logistics_vehicle_rules", ["id"], unique=False)
    op.create_index("ix_lp_vehicle_rules_partner_status", "logistics_vehicle_rules", ["partner_id", "approval_status"], unique=False)
    op.create_index("ix_lp_vehicle_rules_service_area", "logistics_vehicle_rules", ["service_area_id", "approval_status"], unique=False)
    op.create_index("ix_lp_vehicle_rules_route_scope", "logistics_vehicle_rules", ["route_scope", "approval_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lp_vehicle_rules_route_scope", table_name="logistics_vehicle_rules")
    op.drop_index("ix_lp_vehicle_rules_service_area", table_name="logistics_vehicle_rules")
    op.drop_index("ix_lp_vehicle_rules_partner_status", table_name="logistics_vehicle_rules")
    op.drop_index("ix_logistics_vehicle_rules_id", table_name="logistics_vehicle_rules")
    op.drop_table("logistics_vehicle_rules")

    op.drop_index("ix_lp_category_rules_category", table_name="logistics_category_pricing_rules")
    op.drop_index("ix_lp_category_rules_service_area", table_name="logistics_category_pricing_rules")
    op.drop_index("ix_lp_category_rules_partner_status", table_name="logistics_category_pricing_rules")
    op.drop_index("ix_logistics_category_pricing_rules_id", table_name="logistics_category_pricing_rules")
    op.drop_table("logistics_category_pricing_rules")

