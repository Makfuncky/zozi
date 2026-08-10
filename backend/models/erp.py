"""ERP / logistics-trading domain models (schema ``logistics``)."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index,
    Integer, Numeric, String, Text, UniqueConstraint, UUID,
)
from sqlalchemy.orm import relationship

from models import Base
from utils.datetime_utils import utcnow as _utcnow


class Warehouse(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'warehouses'
    __table_args__ = (
                         Index("ix_warehouses_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(30), nullable=False, unique=True, index=True)
    address = Column(String(300), nullable=True)
    city = Column(String(120), nullable=True)
    country_code = Column(String(3), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class PurchaseOrder(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'purchase_orders'
    __table_args__ = (
                         Index("ix_purchase_orders_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(40), nullable=False, unique=True, index=True)
    supplier_id = Column(Integer, ForeignKey('finance.vendors.id', ondelete='RESTRICT'), nullable=True, index=True)
    supplier_name = Column(String(200), nullable=True)
    order_date = Column(DateTime, default=_utcnow)
    expected_delivery_date = Column(DateTime, nullable=True)
    warehouse_id = Column(Integer, ForeignKey('logistics.warehouses.id', ondelete='RESTRICT'), nullable=True, index=True)
    currency = Column(String(3), default='OMR')
    notes = Column(Text, nullable=True)
    terms = Column(Text, nullable=True)
    shipping_address = Column(Text, nullable=True)
    country_code = Column(String(3), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey('security.users.id', ondelete='RESTRICT'), nullable=True, index=True)
    status = Column(String(20), default='draft')
    subtotal = Column(Numeric(14, 2), default=0)
    discount_total = Column(Numeric(14, 2), default=0)
    tax_total = Column(Numeric(14, 2), default=0)
    grand_total = Column(Numeric(14, 2), default=0)
    total_amount = Column(Numeric(14, 2), default=0)
    delivery_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    lines = relationship('PurchaseOrderLine', backref='po', cascade='all, delete-orphan')

class PurchaseOrderLine(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'purchase_order_lines'
    __table_args__ = (
                         Index("ix_purchase_order_lines_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    po_id = Column(Integer, ForeignKey('logistics.purchase_orders.id', ondelete='RESTRICT'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('commerce.products.id', ondelete='RESTRICT'), nullable=True, index=True)
    product_name = Column(String(200), nullable=True)
    sku = Column(String(80), nullable=True)
    description = Column(Text, nullable=True)
    quantity_ordered = Column(Numeric(14, 2), default=0)
    quantity_received = Column(Numeric(14, 2), default=0)
    unit_price = Column(Numeric(14, 2), default=0)
    discount_percent = Column(Numeric(6, 2), default=0)
    discount_amount = Column(Numeric(14, 2), default=0)
    tax_rate = Column(Numeric(6, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    line_total = Column(Numeric(14, 2), default=0)
    weight = Column(Numeric(14, 3), nullable=True)
    volume = Column(Numeric(14, 3), nullable=True)
    country_code = Column(String(3), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class GoodsReceiptNote(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'goods_receipt_notes'
    __table_args__ = (
                         Index("ix_goods_receipt_notes_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    grn_number = Column(String(40), nullable=False, unique=True, index=True)
    po_id = Column(Integer, ForeignKey('logistics.purchase_orders.id', ondelete='RESTRICT'), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey('finance.vendors.id', ondelete='RESTRICT'), nullable=True, index=True)
    receipt_date = Column(DateTime, default=_utcnow)
    warehouse_id = Column(Integer, ForeignKey('logistics.warehouses.id', ondelete='RESTRICT'), nullable=True, index=True)
    status = Column(String(20), default='confirmed')
    notes = Column(Text, nullable=True)
    received_by = Column(Integer, ForeignKey('security.users.id', ondelete='RESTRICT'), nullable=True, index=True)
    country_code = Column(String(3), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    lines = relationship('GoodsReceiptLine', backref='grn', cascade='all, delete-orphan')

class GoodsReceiptLine(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'goods_receipt_lines'
    __table_args__ = (
                         Index("ix_goods_receipt_lines_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    grn_id = Column(Integer, ForeignKey('logistics.goods_receipt_notes.id', ondelete='RESTRICT'), nullable=False, index=True)
    po_line_id = Column(Integer, ForeignKey('logistics.purchase_order_lines.id', ondelete='RESTRICT'), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey('commerce.products.id', ondelete='RESTRICT'), nullable=True, index=True)
    product_name = Column(String(200), nullable=True)
    sku = Column(String(80), nullable=True)
    quantity_received = Column(Numeric(14, 2), default=0)
    quantity_accepted = Column(Numeric(14, 2), default=0)
    quantity_rejected = Column(Numeric(14, 2), default=0)
    rejection_reason = Column(String(200), nullable=True)
    lot_number = Column(String(80), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    unit_cost = Column(Numeric(14, 2), default=0)
    country_code = Column(String(3), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class SalesOrder(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'sales_orders'
    __table_args__ = (
                         Index("ix_sales_orders_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    so_number = Column(String(40), nullable=False, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey('finance.customers.id', ondelete='RESTRICT'), nullable=True, index=True)
    customer_name = Column(String(200), nullable=True)
    customer_po_number = Column(String(80), nullable=True)
    order_date = Column(DateTime, default=_utcnow)
    expected_delivery_date = Column(DateTime, nullable=True)
    warehouse_id = Column(Integer, ForeignKey('logistics.warehouses.id', ondelete='RESTRICT'), nullable=True, index=True)
    currency = Column(String(3), default='OMR')
    shipping_address = Column(Text, nullable=True)
    billing_address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    terms = Column(Text, nullable=True)
    country_code = Column(String(3), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey('security.users.id', ondelete='RESTRICT'), nullable=True, index=True)
    status = Column(String(20), default='draft')
    subtotal = Column(Numeric(14, 2), default=0)
    discount_total = Column(Numeric(14, 2), default=0)
    tax_total = Column(Numeric(14, 2), default=0)
    grand_total = Column(Numeric(14, 2), default=0)
    delivery_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    lines = relationship('SalesOrderLine', backref='so', cascade='all, delete-orphan')

class SalesOrderLine(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'sales_order_lines'
    __table_args__ = (
                         Index("ix_sales_order_lines_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    so_id = Column(Integer, ForeignKey('logistics.sales_orders.id', ondelete='RESTRICT'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('commerce.products.id', ondelete='RESTRICT'), nullable=True, index=True)
    product_name = Column(String(200), nullable=True)
    sku = Column(String(80), nullable=True)
    description = Column(Text, nullable=True)
    quantity_ordered = Column(Numeric(14, 2), default=0)
    quantity_dispatched = Column(Numeric(14, 2), default=0)
    unit_price = Column(Numeric(14, 2), default=0)
    discount_percent = Column(Numeric(6, 2), default=0)
    discount_amount = Column(Numeric(14, 2), default=0)
    tax_rate = Column(Numeric(6, 2), default=0)
    tax_amount = Column(Numeric(14, 2), default=0)
    line_total = Column(Numeric(14, 2), default=0)
    weight = Column(Numeric(14, 3), nullable=True)
    volume = Column(Numeric(14, 3), nullable=True)
    country_code = Column(String(3), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class StockMovement(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'stock_movements'
    __table_args__ = (
                         Index("ix_stock_movements_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('commerce.products.id', ondelete='RESTRICT'), nullable=True, index=True)
    warehouse_id = Column(Integer, ForeignKey('logistics.warehouses.id', ondelete='RESTRICT'), nullable=True, index=True)
    movement_type = Column(String(20), nullable=True)
    reference_type = Column(String(30), nullable=True)
    reference_id = Column(Integer, nullable=True)
    quantity_change = Column(Numeric(14, 2), default=0)
    quantity_after = Column(Numeric(14, 2), default=0)
    unit_cost = Column(Numeric(14, 2), nullable=True)
    total_cost = Column(Numeric(14, 2), default=0)
    country_code = Column(String(3), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey('security.users.id', ondelete='RESTRICT'), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class ImportShipment(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'import_shipments'
    __table_args__ = (
                         Index("ix_import_shipments_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    shipment_ref = Column(String(40), nullable=False, unique=True, index=True)
    po_id = Column(Integer, ForeignKey('logistics.purchase_orders.id', ondelete='RESTRICT'), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey('finance.vendors.id', ondelete='RESTRICT'), nullable=True, index=True)
    supplier_name = Column(String(200), nullable=True)
    origin_country = Column(String(10), nullable=True)
    port_of_loading = Column(String(120), nullable=True)
    port_of_discharge = Column(String(120), nullable=True)
    vessel_name = Column(String(160), nullable=True)
    bill_of_lading = Column(String(120), nullable=True)
    container_number = Column(String(80), nullable=True)
    shipment_date = Column(DateTime, default=_utcnow)
    estimated_arrival = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    currency = Column(String(3), default='OMR')
    exchange_rate = Column(Numeric(14, 6), default=1)
    warehouse_id = Column(Integer, ForeignKey('logistics.warehouses.id', ondelete='RESTRICT'), nullable=True, index=True)
    country_code = Column(String(3), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey('security.users.id', ondelete='RESTRICT'), nullable=True, index=True)
    status = Column(String(20), default='draft')
    product_cost_total = Column(Numeric(14, 2), default=0)
    freight_cost = Column(Numeric(14, 2), default=0)
    insurance_cost = Column(Numeric(14, 2), default=0)
    port_charges = Column(Numeric(14, 2), default=0)
    inland_freight = Column(Numeric(14, 2), default=0)
    bank_charges = Column(Numeric(14, 2), default=0)
    other_costs = Column(Numeric(14, 2), default=0)
    total_landed_cost = Column(Numeric(14, 2), default=0)
    duty_cost = Column(Numeric(14, 2), default=0)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime(), default=_utcnow, onupdate=_utcnow)
    lines = relationship('ImportShipmentLine', backref='shipment', cascade='all, delete-orphan')

class ImportShipmentLine(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'import_shipment_lines'
    __table_args__ = (
                         Index("ix_import_shipment_lines_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey('logistics.import_shipments.id', ondelete='RESTRICT'), nullable=False, index=True)
    po_line_id = Column(Integer, ForeignKey('logistics.purchase_order_lines.id', ondelete='RESTRICT'), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey('commerce.products.id', ondelete='RESTRICT'), nullable=True, index=True)
    product_name = Column(String(200), nullable=True)
    sku = Column(String(80), nullable=True)
    hs_code = Column(String(40), nullable=True)
    quantity = Column(Numeric(14, 2), default=0)
    unit_cost_fx = Column(Numeric(14, 2), default=0)
    unit_cost_local = Column(Numeric(14, 2), default=0)
    line_total_fx = Column(Numeric(14, 2), default=0)
    weight_kg = Column(Numeric(14, 3), nullable=True)
    volume_cbm = Column(Numeric(14, 3), nullable=True)
    allocated_freight = Column(Numeric(14, 2), default=0)
    allocated_insurance = Column(Numeric(14, 2), default=0)
    allocated_port = Column(Numeric(14, 2), default=0)
    allocated_other = Column(Numeric(14, 2), default=0)
    duty_amount = Column(Numeric(14, 2), default=0)
    landed_unit_cost = Column(Numeric(14, 4), default=0)
    country_code = Column(String(3), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class LandedCostAllocation(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'landed_cost_allocations'
    __table_args__ = (
                         Index("ix_landed_cost_allocations_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey('logistics.import_shipments.id', ondelete='RESTRICT'), nullable=False, index=True)
    cost_type = Column(String(30), nullable=True)
    description = Column(Text, nullable=True)
    total_amount = Column(Numeric(14, 2), default=0)
    allocation_method = Column(String(20), nullable=True)
    currency = Column(String(3), default='OMR')
    exchange_rate = Column(Numeric(14, 6), default=1)
    country_code = Column(String(3), nullable=True, index=True)
    status = Column(String(20), default='allocated')
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class CustomsEntry(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'customs_entries'
    __table_args__ = (
                         Index("ix_customs_entries_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey('logistics.import_shipments.id', ondelete='RESTRICT'), nullable=False, index=True)
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
    country_code = Column(String(3), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

class ImportCostTemplate(Base):
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1, nullable=False, server_default='1')
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    __tablename__ = 'import_cost_templates'
    __table_args__ = (
                         Index("ix_import_cost_templates_country_created", "country_code", "created_at"),
                         {'schema': 'logistics'},
                     )
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(160), nullable=False)
    default_duty_rate = Column(Numeric(6, 2), nullable=True)
    default_freight_percent = Column(Numeric(6, 2), nullable=True)
    default_insurance_percent = Column(Numeric(6, 2), nullable=True)
    default_port_charges_percent = Column(Numeric(6, 2), nullable=True)
    default_bank_charges_percent = Column(Numeric(6, 2), nullable=True)
    allocation_method = Column(String(20), default='by_value')
    country_code = Column(String(3), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
