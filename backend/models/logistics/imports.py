from __future__ import annotations

from db.mixins import AuditMixin, SoftDeleteMixin

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from utils.datetime_utils import utcnow as _utcnow

from models import Base

__all__ = [
    "ImportShipment", "ImportShipmentLine", "LandedCostAllocation",
    "CustomsEntry", "ImportCostTemplate",
]


class ImportShipment(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "import_shipments"
    __table_args__ = (
        Index("ix_import_shipments_status", "status"),
        Index("ix_import_shipments_country", "country_code"),
        Index("ix_import_shipments_po", "po_id"),
        Index("ix_import_shipments_country_created", "country_code", "created_at"),
        {"schema": "logistics"},
    )
    id = Column(Integer, primary_key=True, index=True)
    shipment_ref = Column(String(30), unique=True, nullable=False, index=True)
    po_id = Column(Integer, nullable=True)
    supplier_id = Column(Integer, nullable=True, index=True)
    supplier_name = Column(String(200), nullable=True)
    origin_country = Column(String(100), nullable=True)
    port_of_loading = Column(String(100), nullable=True)
    port_of_discharge = Column(String(100), nullable=True)
    vessel_name = Column(String(100), nullable=True)
    bill_of_lading = Column(String(100), nullable=True)
    container_number = Column(String(50), nullable=True)
    shipment_date = Column(DateTime, nullable=True)
    estimated_arrival_at = Column(DateTime, nullable=True)
    actual_arrival_at = Column(DateTime, nullable=True)
    currency = Column(String(10), default="OMR")
    exchange_rate = Column(Numeric(18, 6), default=1)
    warehouse_id = Column(Integer, ForeignKey("logistics.warehouses.id", ondelete="RESTRICT"), nullable=True, index=True)
    country_code = Column(String(10), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    status = Column(String(20), default="draft")  # draft, in_transit, customs_cleared, landed
    product_cost_total = Column(Numeric(18, 2), nullable=True)
    freight_cost = Column(Numeric(18, 2), nullable=True)
    insurance_cost = Column(Numeric(18, 2), nullable=True)
    port_charges = Column(Numeric(18, 2), nullable=True)
    inland_freight = Column(Numeric(18, 2), nullable=True)
    bank_charges = Column(Numeric(18, 2), nullable=True)
    other_costs = Column(Numeric(18, 2), nullable=True)
    duty_cost = Column(Numeric(18, 2), nullable=True)
    total_landed_cost = Column(Numeric(18, 2), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)

    lines = relationship("ImportShipmentLine", back_populates="shipment",
                         cascade="all, delete-orphan", lazy="selectin")


class ImportShipmentLine(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "import_shipment_lines"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("logistics.import_shipments.id", ondelete="RESTRICT"), nullable=False, index=True)
    po_line_id = Column(Integer, nullable=True)
    product_id = Column(Integer, nullable=True, index=True)
    product_name = Column(String(255), nullable=True)
    sku = Column(String(100), nullable=True)
    hs_code = Column(String(50), nullable=True)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost_fx = Column(Numeric(18, 6), nullable=True)
    unit_cost_local = Column(Numeric(18, 6), nullable=True)
    line_total_fx = Column(Numeric(18, 6), nullable=True)
    weight_kg = Column(Numeric(12, 4), nullable=True)
    volume_cbm = Column(Numeric(12, 4), nullable=True)
    country_code = Column(String(10), nullable=True)
    allocated_freight = Column(Numeric(18, 2), default=0)
    allocated_insurance = Column(Numeric(18, 2), default=0)
    allocated_port = Column(Numeric(18, 2), default=0)
    allocated_other = Column(Numeric(18, 2), default=0)
    duty_amount = Column(Numeric(18, 2), default=0)
    landed_unit_cost = Column(Numeric(18, 6), nullable=True)

    shipment = relationship("ImportShipment", back_populates="lines")


class LandedCostAllocation(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "landed_cost_allocations"
    __table_args__ = (
        Index("ix_landed_cost_alloc_shipment", "shipment_id"),
        Index("ix_landed_cost_allocations_country_created", "country_code", "created_at"),
        {"schema": "logistics"},
    )
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("logistics.import_shipments.id", ondelete="RESTRICT"), nullable=False, index=True)
    cost_type = Column(String(30), nullable=False)  # freight, insurance, port_charges, inland_freight, bank_charges, other_costs
    description = Column(String(255), nullable=True)
    total_amount = Column(Numeric(18, 2), nullable=False)
    allocation_method = Column(String(20), default="by_value")  # by_value, by_weight, by_volume, by_quantity
    currency = Column(String(10), default="OMR")
    exchange_rate = Column(Numeric(18, 6), nullable=True)
    country_code = Column(String(10), nullable=True)
    status = Column(String(20), default="allocated")
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)


class CustomsEntry(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "customs_entries"
    __table_args__ = (
        Index("ix_customs_entries_shipment", "shipment_id"),
        Index("ix_customs_entries_country_created", "country_code", "created_at"),
        {"schema": "logistics"},
    )
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("logistics.import_shipments.id", ondelete="RESTRICT"), nullable=False, index=True)
    customs_declaration_number = Column(String(50), nullable=True)
    customs_broker = Column(String(100), nullable=True)
    entry_date = Column(DateTime, nullable=True)
    duty_rate_applied = Column(Numeric(8, 4), nullable=True)
    duty_amount = Column(Numeric(18, 2), default=0)
    vat_on_duty = Column(Numeric(18, 2), default=0)
    penalties = Column(Numeric(18, 2), default=0)
    total_customs_cost = Column(Numeric(18, 2), nullable=True)
    status = Column(String(20), default="cleared")
    notes = Column(Text, nullable=True)
    country_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    created_by = Column(Integer, nullable=True)


class ImportCostTemplate(Base, AuditMixin, SoftDeleteMixin):
    __tablename__ = "import_cost_templates"
    __table_args__ = (
        UniqueConstraint("name", "country_code", name="uq_import_cost_template_name_country"),
        {"schema": "logistics"},
    )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    default_duty_rate = Column(Numeric(8, 4), nullable=True)
    default_freight_percent = Column(Numeric(8, 4), nullable=True)
    default_insurance_percent = Column(Numeric(8, 4), nullable=True)
    default_port_charges_percent = Column(Numeric(8, 4), nullable=True)
    default_bank_charges_percent = Column(Numeric(8, 4), nullable=True)
    allocation_method = Column(String(20), default="by_value")
    country_code = Column(String(10), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
