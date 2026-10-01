"""Add materialized views for analytics and dashboards

Revision ID: 20260831_0005
Revises: 20260831_0004
Create Date: 2026-08-31
"""
import sqlalchemy as sa
from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import quoted_name as sql_identifier

revision: str = "20260831_0005"
down_revision: Union[str, None] = "20260831_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VIEW_DDL = {
    "analytics.mv_daily_sales": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_daily_sales AS
        SELECT
            country_code,
            DATE(created_at) AS sale_date,
            COUNT(*) AS order_count,
            SUM(total_amount) AS total_revenue,
            AVG(total_amount) AS avg_order_value
        FROM commerce.orders
        WHERE is_deleted = false
        GROUP BY country_code, DATE(created_at)
        WITH DATA
    """,
    "analytics.mv_product_performance": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_product_performance AS
        SELECT
            p.id AS product_id,
            p.name AS product_name,
            p.country_code,
            COUNT(oi.id) AS times_ordered,
            SUM(oi.quantity) AS total_quantity_sold,
            SUM(oi.price * oi.total) AS total_revenue
        FROM commerce.products p
        LEFT JOIN commerce.order_items oi ON p.id = oi.product_id
        WHERE p.is_deleted = false
        GROUP BY p.id, p.name, p.country_code
        WITH DATA
    """,
    "analytics.mv_supplier_performance": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_supplier_performance AS
        SELECT
            sp.id AS supplier_id,
            sp.business_name,
            sp.country_code,
            COUNT(p.id) AS product_count,
            COALESCE(SUM(oi.quantity), 0) AS total_items_sold
        FROM supplier.supplier_profiles sp
        LEFT JOIN commerce.products p ON sp.user_id = p.supplier_id
        LEFT JOIN commerce.order_items oi ON p.id = oi.product_id
        WHERE sp.is_deleted = false
        GROUP BY sp.id, sp.business_name, sp.country_code
        WITH DATA
    """,
    "analytics.kpi_customer": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.kpi_customer AS
        SELECT
            country_code,
            COUNT(*) AS total_customers,
            COUNT(*) FILTER (WHERE is_active = true) AS active_customers,
            COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') AS new_customers_30d
        FROM customer.customers
        WHERE is_deleted = false
        GROUP BY country_code
        WITH DATA
    """,
    "analytics.kpi_revenue": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.kpi_revenue AS
        SELECT
            country_code,
            SUM(total_amount) AS total_revenue,
            COUNT(*) AS total_orders,
            AVG(total_amount) AS avg_order_value
        FROM commerce.orders
        WHERE is_deleted = false AND status_code NOT IN ('cancelled', 'returned')
        GROUP BY country_code
        WITH DATA
    """,
    "analytics.kpi_country": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.kpi_country AS
        SELECT
            cc.code AS country_code,
            cc.name AS country_name,
            cc.currency,
            (SELECT COUNT(*) FROM commerce.orders o WHERE o.country_code = cc.code AND o.is_deleted = false) AS total_orders,
            (SELECT COUNT(*) FROM customer.customers cu WHERE cu.country_code = cc.code AND cu.is_deleted = false) AS total_customers,
            (SELECT COUNT(*) FROM supplier.supplier_profiles sp WHERE sp.country_code = cc.code AND sp.is_deleted = false) AS total_suppliers
        FROM country.country_configs cc
        WHERE cc.is_active = true
        WITH DATA
    """,
    "analytics.mv_facet_counts": """
        CREATE MATERIALIZED VIEW IF NOT EXISTS analytics.mv_facet_counts AS
        SELECT
            country_code,
            category_id,
            brand,
            color,
            COUNT(*) AS product_count,
            MIN(price) AS min_price,
            MAX(price) AS max_price
        FROM commerce.products
        WHERE is_active = true AND is_deleted = false
        GROUP BY country_code, category_id, brand, color
        WITH DATA
    """,
}

INDEX_DDL = [
    "CREATE INDEX IF NOT EXISTS ix_mv_daily_sales_country ON analytics.mv_daily_sales(country_code)",
    "CREATE INDEX IF NOT EXISTS ix_mv_daily_sales_date ON analytics.mv_daily_sales(sale_date)",
    "CREATE INDEX IF NOT EXISTS ix_mv_product_perf_country ON analytics.mv_product_performance(country_code)",
    "CREATE INDEX IF NOT EXISTS ix_kpi_customer_country ON analytics.kpi_customer(country_code)",
    "CREATE INDEX IF NOT EXISTS ix_kpi_revenue_country ON analytics.kpi_revenue(country_code)",
]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return  # Materialized views not supported in SQLite

    # ── Materialized Views (from document §2.15 / §7.3) ─────────────────────
    for ddl in VIEW_DDL.values():
        op.execute(sa.text(ddl))

    # Create indexes on materialized views
    for ddl in INDEX_DDL:
        op.execute(sa.text(ddl))


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        return

    # Drop materialized views
    for view_name in [
        "analytics.mv_facet_counts",
        "analytics.kpi_country",
        "analytics.kpi_revenue",
        "analytics.kpi_customer",
        "analytics.mv_supplier_performance",
        "analytics.mv_product_performance",
        "analytics.mv_daily_sales",
    ]:
        v = sql_identifier(view_name)
        op.execute(
            sa.text("DROP MATERIALIZED VIEW IF EXISTS :v"),
            {"v": v},
        )
