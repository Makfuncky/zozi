"""ERP / finance domain models (schema ``finance``).

Logistics-related models (Warehouse, PurchaseOrder, GoodsReceiptNote, SalesOrder,
StockMovement, ImportShipment, and their line items) have been moved to
``domains.logistics.models.erp`` per ARCHITECTURE_DIAGRAM.md domain boundaries.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint, UUID,
)
from sqlalchemy.orm import relationship

from infrastructure.database.base import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class LandedCostAllocation(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by_id = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'landed_cost_allocations'
    __table_args__ = (
                         Index("ix_landed_cost_allocations_country_created", "country_code", "created_at"),
                         {'schema': 'finance'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey('finance.import_shipments.id', ondelete='RESTRICT'), nullable=False, index=True)
    cost_type = Column(String(30), nullable=True)
    description = Column(Text, nullable=True)
    total_amount = Column(Numeric(14, 2), default=0)
    allocation_method = Column(String(20), nullable=True)
    currency = Column(String(3), default='OMR')
    exchange_rate = Column(Numeric(14, 6), default=1)
    country_code = Column(String(2), nullable=True, index=True)
    status = Column(String(20), default='allocated')
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class CustomsEntry(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by_id = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'customs_entries'
    __table_args__ = (
                         Index("ix_customs_entries_country_created", "country_code", "created_at"),
                         {'schema': 'finance'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey('finance.import_shipments.id', ondelete='RESTRICT'), nullable=False, index=True)
    customs_declaration_number = Column(String(80), nullable=True)
    customs_broker = Column(String(160), nullable=True)
    entry_date = Column(DateTime, default=_utcnow)
    duty_rate_applied = Column(Numeric(6, 2), nullable=True)
    duty_amount = Column(Numeric(14, 2), default=0)
    vat_on_duty = Column(Numeric(14, 2), default=0)
    penalties = Column(Numeric(14, 2), default=0)
    total_customs_cost = Column(Numeric(14, 2), default=0)
    status = Column(String(20), default='cleared')
    notes = Column(Text, nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class ImportCostTemplate(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by_id = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'import_cost_templates'
    __table_args__ = (
                         Index("ix_import_cost_templates_country_created", "country_code", "created_at"),
                         {'schema': 'finance'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(160), nullable=False)
    default_duty_rate = Column(Numeric(6, 2), nullable=True)
    default_freight_percent = Column(Numeric(6, 2), nullable=True)
    default_insurance_percent = Column(Numeric(6, 2), nullable=True)
    default_port_charges_percent = Column(Numeric(6, 2), nullable=True)
    default_bank_charges_percent = Column(Numeric(6, 2), nullable=True)
    allocation_method = Column(String(20), default='by_value')
    country_code = Column(String(2), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
