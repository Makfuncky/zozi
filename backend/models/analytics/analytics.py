"""Analytics snapshot / materialized-view read models (Constitution §2.15, ADR-008).

Snapshot tables refreshed by cron — never live aggregates on the transactional DB.
"""
from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from utils.datetime_utils import utcnow as _utcnow

from . import Base

__all__ = [
    "DailySalesSnapshot",
    "MonthlySalesSnapshot",
    "KPICustomer",
    "KPISupplier",
    "KPICountry",
    "KPIRevenue",
    "KPIOrders",
    "KPIRetention",
    "KPIConversion",
    "CashPositionSnapshotMV",
    "FacetCountsSnapshot",
]

_SCHEMA = {"schema": "analytics"}


class DailySalesSnapshot(Base):
    """Daily sales snapshot per country/currency."""
    __tablename__ = "mv_daily_sales"
    __table_args__ = (
        UniqueConstraint("country_code", "snapshot_date", "currency", name="uq_mv_daily_sales"),
        Index("ix_mv_daily_sales_date", "snapshot_date"), _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    currency = Column(String(3), nullable=False, default="OMR")
    total_orders = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Numeric(14, 2), nullable=False, default=0)
    total_gross_sales = Column(Numeric(14, 2), nullable=False, default=0)
    total_net_sales = Column(Numeric(14, 2), nullable=False, default=0)
    total_refunds = Column(Numeric(14, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class MonthlySalesSnapshot(Base):
    """Monthly sales rollup per country/currency."""
    __tablename__ = "mv_monthly_sales"
    __table_args__ = (
        UniqueConstraint("country_code", "period_year", "period_month", "currency", name="uq_mv_monthly_sales"),
        Index("ix_mv_monthly_sales_period", "period_year", "period_month"), _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    period_year = Column(Integer, nullable=False)
    period_month = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="OMR")
    total_orders = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Numeric(14, 2), nullable=False, default=0)
    total_gross_sales = Column(Numeric(14, 2), nullable=False, default=0)
    total_net_sales = Column(Numeric(14, 2), nullable=False, default=0)
    total_refunds = Column(Numeric(14, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class KPICustomer(Base):
    """Customer-level KPIs per country/day."""
    __tablename__ = "kpi_customer"
    __table_args__ = (
        UniqueConstraint("country_code", "kpi_date", name="uq_kpi_customer"),
        _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    kpi_date = Column(Date, nullable=False, index=True)
    new_customers = Column(Integer, nullable=False, default=0)
    active_customers = Column(Integer, nullable=False, default=0)
    total_customers = Column(Integer, nullable=False, default=0)
    repeat_customers = Column(Integer, nullable=False, default=0)
    churned_customers = Column(Integer, nullable=False, default=0)
    customer_lifetime_value = Column(Numeric(14, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class KPISupplier(Base):
    """Supplier-level KPIs per country/day."""
    __tablename__ = "kpi_supplier"
    __table_args__ = (
        UniqueConstraint("country_code", "kpi_date", name="uq_kpi_supplier"),
        _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    kpi_date = Column(Date, nullable=False, index=True)
    new_suppliers = Column(Integer, nullable=False, default=0)
    active_suppliers = Column(Integer, nullable=False, default=0)
    total_suppliers = Column(Integer, nullable=False, default=0)
    avg_products_per_supplier = Column(Numeric(10, 2), nullable=False, default=0)
    fulfillment_rate = Column(Numeric(5, 4), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class KPICountry(Base):
    """Country-level commercial KPIs per day."""
    __tablename__ = "kpi_country"
    __table_args__ = (
        UniqueConstraint("country_code", "kpi_date", name="uq_kpi_country"),
        _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    kpi_date = Column(Date, nullable=False, index=True)
    gmv = Column(Numeric(14, 2), nullable=False, default=0)
    revenue = Column(Numeric(14, 2), nullable=False, default=0)
    orders_count = Column(Integer, nullable=False, default=0)
    active_users = Column(Integer, nullable=False, default=0)
    conversion_rate = Column(Numeric(5, 4), nullable=False, default=0)
    avg_order_value = Column(Numeric(14, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class KPIRevenue(Base):
    """Revenue composition KPIs per country/day."""
    __tablename__ = "kpi_revenue"
    __table_args__ = (
        UniqueConstraint("country_code", "kpi_date", name="uq_kpi_revenue"),
        _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    kpi_date = Column(Date, nullable=False, index=True)
    gross_revenue = Column(Numeric(14, 2), nullable=False, default=0)
    net_revenue = Column(Numeric(14, 2), nullable=False, default=0)
    refunds = Column(Numeric(14, 2), nullable=False, default=0)
    chargebacks = Column(Numeric(14, 2), nullable=False, default=0)
    platform_commission = Column(Numeric(14, 2), nullable=False, default=0)
    logistics_revenue = Column(Numeric(14, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class KPIOrders(Base):
    """Order-funnel KPIs per country/day."""
    __tablename__ = "kpi_orders"
    __table_args__ = (
        UniqueConstraint("country_code", "kpi_date", name="uq_kpi_orders"),
        _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    kpi_date = Column(Date, nullable=False, index=True)
    total_orders = Column(Integer, nullable=False, default=0)
    completed_orders = Column(Integer, nullable=False, default=0)
    cancelled_orders = Column(Integer, nullable=False, default=0)
    returned_orders = Column(Integer, nullable=False, default=0)
    avg_order_value = Column(Numeric(14, 2), nullable=False, default=0)
    on_time_delivery_rate = Column(Numeric(5, 4), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class KPIRetention(Base):
    """Cohort retention KPIs per country/month."""
    __tablename__ = "kpi_retention"
    __table_args__ = (
        UniqueConstraint("country_code", "cohort_month", name="uq_kpi_retention"),
        _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    cohort_month = Column(String(7), nullable=False, index=True)  # YYYY-MM
    retained_customers = Column(Integer, nullable=False, default=0)
    retention_rate_1m = Column(Numeric(5, 4), nullable=False, default=0)
    retention_rate_3m = Column(Numeric(5, 4), nullable=False, default=0)
    retention_rate_6m = Column(Numeric(5, 4), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class KPIConversion(Base):
    """Conversion-funnel KPIs per country/day."""
    __tablename__ = "kpi_conversion"
    __table_args__ = (
        UniqueConstraint("country_code", "kpi_date", name="uq_kpi_conversion"),
        _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    kpi_date = Column(Date, nullable=False, index=True)
    sessions = Column(Integer, nullable=False, default=0)
    unique_visitors = Column(Integer, nullable=False, default=0)
    add_to_cart_rate = Column(Numeric(5, 4), nullable=False, default=0)
    checkout_conversion_rate = Column(Numeric(5, 4), nullable=False, default=0)
    cart_abandonment_rate = Column(Numeric(5, 4), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class CashPositionSnapshotMV(Base):
    """Daily cash position snapshot per country/currency."""
    __tablename__ = "mv_cash_position"
    __table_args__ = (
        UniqueConstraint("country_code", "snapshot_date", "currency", name="uq_mv_cash_position"),
        _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    currency = Column(String(3), nullable=False, default="OMR")
    total_cash = Column(Numeric(14, 2), nullable=False, default=0)
    cash_in_banks = Column(Numeric(14, 2), nullable=False, default=0)
    cash_in_transit = Column(Numeric(14, 2), nullable=False, default=0)
    pending_payouts = Column(Numeric(14, 2), nullable=False, default=0)
    pending_settlements = Column(Numeric(14, 2), nullable=False, default=0)
    net_cash_position = Column(Numeric(14, 2), nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)


class FacetCountsSnapshot(Base):
    """Facet / category counts snapshot for search facets."""
    __tablename__ = "mv_facet_counts"
    __table_args__ = (
        UniqueConstraint("country_code", "facet_type", "facet_value", "snapshot_date", name="uq_mv_facet_counts"),
        Index("ix_mv_facet_counts_type", "facet_type"), _SCHEMA,
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    facet_type = Column(String(50), nullable=False)  # category | brand | attribute | price_range
    facet_value = Column(String(200), nullable=False)
    item_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
