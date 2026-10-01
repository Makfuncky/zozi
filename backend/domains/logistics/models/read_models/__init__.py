"""logistics domain — CQRS-lite read models (projections).

These models are optimized for read-heavy queries and denormalize data from
multiple tables to avoid expensive joins at query time. They are populated by
domain events and read-only from the application layer.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, JSON, Index
from sqlalchemy import func

from infrastructure.database.base import Base

__all__ = [
    "ShipmentTrackingProjection",
    "PartnerPerformanceProjection",
]


class ShipmentTrackingProjection(Base):
    __tablename__ = "shipment_tracking_projections"
    __table_args__ = (
        Index("ix_shipment_tracking_order_id", "order_id"),
        Index("ix_shipment_tracking_status", "status_code"),
        {"schema": "logistics"},
    )

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(Integer, nullable=False)
    status_code = Column(String(50), nullable=False)
    carrier_name = Column(String(255), nullable=True)
    tracking_number = Column(String(255), nullable=True)
    current_hub = Column(String(255), nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    actual_delivery = Column(DateTime, nullable=True)
    event_log = Column(JSON, nullable=True)
    last_event_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PartnerPerformanceProjection(Base):
    __tablename__ = "partner_performance_projections"
    __table_args__ = (
        Index("ix_partner_perf_partner_id", "partner_id"),
        Index("ix_partner_perf_country", "country_code"),
        {"schema": "logistics"},
    )

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id", ondelete="CASCADE"), nullable=False, index=True)
    country_code = Column(String(2), nullable=True)
    total_shipments = Column(Integer, default=0)
    delivered_shipments = Column(Integer, default=0)
    cancelled_shipments = Column(Integer, default=0)
    avg_delivery_hours = Column(Numeric(10, 2), nullable=True)
    on_time_rate = Column(Numeric(5, 4), nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
