"""create_analytics_snapshot_tables

Revision ID: 20260730_0009
Revises: 20260730_0008
Create Date: 2026-07-30
"""
import os
import sys
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(_project_root, "alembic"))
sys.path.insert(0, _project_root)

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op
from migration_helpers import safe_create_index, safe_create_table, safe_drop_table

revision: str = "20260730_0009"
down_revision: Union[str, None] = "20260730_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_cols() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    ]


def _numeric(prec: int = 14, scale: int = 2) -> sa.Numeric:
    return sa.Numeric(prec, scale)


def upgrade() -> None:
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"
    schema = None if is_sqlite else "analytics"

    safe_create_table(op, 
        "mv_daily_sales",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="OMR"),
        sa.Column("total_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_revenue", _numeric(), nullable=False, server_default="0"),
        sa.Column("total_gross_sales", _numeric(), nullable=False, server_default="0"),
        sa.Column("total_net_sales", _numeric(), nullable=False, server_default="0"),
        sa.Column("total_refunds", _numeric(), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "snapshot_date", "currency", name="uq_mv_daily_sales"),
        schema=schema,
    )
    safe_create_index(op, "ix_mv_daily_sales_date", "mv_daily_sales", ["snapshot_date"], schema=schema)
    safe_create_index(op, "ix_mv_daily_sales_country_code", "mv_daily_sales", ["country_code"], schema=schema)

    safe_create_table(op, 
        "mv_monthly_sales",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="OMR"),
        sa.Column("total_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_revenue", _numeric(), nullable=False, server_default="0"),
        sa.Column("total_gross_sales", _numeric(), nullable=False, server_default="0"),
        sa.Column("total_net_sales", _numeric(), nullable=False, server_default="0"),
        sa.Column("total_refunds", _numeric(), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "period_year", "period_month", "currency", name="uq_mv_monthly_sales"),
        schema=schema,
    )
    safe_create_index(op, "ix_mv_monthly_sales_period", "mv_monthly_sales", ["period_year", "period_month"], schema=schema)
    safe_create_index(op, "ix_mv_monthly_sales_country_code", "mv_monthly_sales", ["country_code"], schema=schema)

    safe_create_table(op, 
        "kpi_customer",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("kpi_date", sa.Date(), nullable=False),
        sa.Column("new_customers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_customers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_customers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repeat_customers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("churned_customers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("customer_lifetime_value", _numeric(), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "kpi_date", name="uq_kpi_customer"),
        schema=schema,
    )
    safe_create_index(op, "ix_kpi_customer_kpi_date", "kpi_customer", ["kpi_date"], schema=schema)
    safe_create_index(op, "ix_kpi_customer_country_code", "kpi_customer", ["country_code"], schema=schema)

    safe_create_table(op, 
        "kpi_supplier",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("kpi_date", sa.Date(), nullable=False),
        sa.Column("new_suppliers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_suppliers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_suppliers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_products_per_supplier", _numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("fulfillment_rate", _numeric(5, 4), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "kpi_date", name="uq_kpi_supplier"),
        schema=schema,
    )
    safe_create_index(op, "ix_kpi_supplier_kpi_date", "kpi_supplier", ["kpi_date"], schema=schema)
    safe_create_index(op, "ix_kpi_supplier_country_code", "kpi_supplier", ["country_code"], schema=schema)

    safe_create_table(op, 
        "kpi_country",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("kpi_date", sa.Date(), nullable=False),
        sa.Column("gmv", _numeric(), nullable=False, server_default="0"),
        sa.Column("revenue", _numeric(), nullable=False, server_default="0"),
        sa.Column("orders_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conversion_rate", _numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("avg_order_value", _numeric(), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "kpi_date", name="uq_kpi_country"),
        schema=schema,
    )
    safe_create_index(op, "ix_kpi_country_kpi_date", "kpi_country", ["kpi_date"], schema=schema)
    safe_create_index(op, "ix_kpi_country_country_code", "kpi_country", ["country_code"], schema=schema)

    safe_create_table(op, 
        "kpi_revenue",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("kpi_date", sa.Date(), nullable=False),
        sa.Column("gross_revenue", _numeric(), nullable=False, server_default="0"),
        sa.Column("net_revenue", _numeric(), nullable=False, server_default="0"),
        sa.Column("refunds", _numeric(), nullable=False, server_default="0"),
        sa.Column("chargebacks", _numeric(), nullable=False, server_default="0"),
        sa.Column("platform_commission", _numeric(), nullable=False, server_default="0"),
        sa.Column("logistics_revenue", _numeric(), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "kpi_date", name="uq_kpi_revenue"),
        schema=schema,
    )
    safe_create_index(op, "ix_kpi_revenue_kpi_date", "kpi_revenue", ["kpi_date"], schema=schema)
    safe_create_index(op, "ix_kpi_revenue_country_code", "kpi_revenue", ["country_code"], schema=schema)

    safe_create_table(op, 
        "kpi_orders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("kpi_date", sa.Date(), nullable=False),
        sa.Column("total_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancelled_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("returned_orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_order_value", _numeric(), nullable=False, server_default="0"),
        sa.Column("on_time_delivery_rate", _numeric(5, 4), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "kpi_date", name="uq_kpi_orders"),
        schema=schema,
    )
    safe_create_index(op, "ix_kpi_orders_kpi_date", "kpi_orders", ["kpi_date"], schema=schema)
    safe_create_index(op, "ix_kpi_orders_country_code", "kpi_orders", ["country_code"], schema=schema)

    safe_create_table(op, 
        "kpi_retention",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("cohort_month", sa.String(length=7), nullable=False),
        sa.Column("retained_customers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retention_rate_1m", _numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("retention_rate_3m", _numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("retention_rate_6m", _numeric(5, 4), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "cohort_month", name="uq_kpi_retention"),
        schema=schema,
    )
    safe_create_index(op, "ix_kpi_retention_cohort_month", "kpi_retention", ["cohort_month"], schema=schema)
    safe_create_index(op, "ix_kpi_retention_country_code", "kpi_retention", ["country_code"], schema=schema)

    safe_create_table(op, 
        "kpi_conversion",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("kpi_date", sa.Date(), nullable=False),
        sa.Column("sessions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_visitors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("add_to_cart_rate", _numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("checkout_conversion_rate", _numeric(5, 4), nullable=False, server_default="0"),
        sa.Column("cart_abandonment_rate", _numeric(5, 4), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "kpi_date", name="uq_kpi_conversion"),
        schema=schema,
    )
    safe_create_index(op, "ix_kpi_conversion_kpi_date", "kpi_conversion", ["kpi_date"], schema=schema)
    safe_create_index(op, "ix_kpi_conversion_country_code", "kpi_conversion", ["country_code"], schema=schema)

    safe_create_table(op, 
        "mv_cash_position",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="OMR"),
        sa.Column("total_cash", _numeric(), nullable=False, server_default="0"),
        sa.Column("cash_in_banks", _numeric(), nullable=False, server_default="0"),
        sa.Column("cash_in_transit", _numeric(), nullable=False, server_default="0"),
        sa.Column("pending_payouts", _numeric(), nullable=False, server_default="0"),
        sa.Column("pending_settlements", _numeric(), nullable=False, server_default="0"),
        sa.Column("net_cash_position", _numeric(), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "snapshot_date", "currency", name="uq_mv_cash_position"),
        schema=schema,
    )
    safe_create_index(op, "ix_mv_cash_position_snapshot_date", "mv_cash_position", ["snapshot_date"], schema=schema)
    safe_create_index(op, "ix_mv_cash_position_country_code", "mv_cash_position", ["country_code"], schema=schema)

    safe_create_table(op, 
        "mv_facet_counts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("country_code", sa.String(length=3), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("facet_type", sa.String(length=50), nullable=False),
        sa.Column("facet_value", sa.String(length=200), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        *_audit_cols(),
        sa.UniqueConstraint("country_code", "facet_type", "facet_value", "snapshot_date", name="uq_mv_facet_counts"),
        schema=schema,
    )
    safe_create_index(op, "ix_mv_facet_counts_type", "mv_facet_counts", ["facet_type"], schema=schema)
    safe_create_index(op, "ix_mv_facet_counts_country_code", "mv_facet_counts", ["country_code"], schema=schema)
    safe_create_index(op, "ix_mv_facet_counts_snapshot_date", "mv_facet_counts", ["snapshot_date"], schema=schema)


def downgrade() -> None:
    conn = op.get_bind()
    is_sqlite = conn.dialect.name == "sqlite"
    schema = None if is_sqlite else "analytics"

    for table in (
        "mv_facet_counts",
        "mv_cash_position",
        "kpi_conversion",
        "kpi_retention",
        "kpi_orders",
        "kpi_revenue",
        "kpi_country",
        "kpi_supplier",
        "kpi_customer",
        "mv_monthly_sales",
        "mv_daily_sales",
    ):
        safe_drop_table(op, table, schema=schema)
