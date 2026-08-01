from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship, synonym
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = [
    "Order", "OrderItem", "OrderLogisticsAllocation",
    "ReturnRequest", "OrderNotification"
]


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_user_id", "user_id"),
        Index("ix_orders_customer_id", "customer_id"),
        Index("ix_orders_status", "status"), {"schema": "commerce"})
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    status = Column(String, default="pending")
    status_label = Column(String(50), nullable=True)
    payment_status = Column(String, default="pending")
    payment_method = Column(String, nullable=True)
    payment_provider = Column(String, nullable=True)
    payment_intent_id = Column(String, nullable=True)
    subtotal = Column(Numeric(10, 2))
    subtotal_amount = Column(Numeric(10, 2))
    shipping_fee = Column(Numeric(10, 2), default=0)
    shipping_amount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    vat_amount = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2))
    total_amount = Column(Numeric(10, 2))
    coupon_code = Column(String, nullable=True)
    fraud_score = Column(Numeric(5, 2), default=0)
    fraud_action = Column(String, default="allow")
    currency = Column(String, default="USD")
    shipping_address = Column(Text, nullable=True)
    shipping_city = Column(String, nullable=True)
    shipping_country = Column(String, nullable=True)
    shipping_postal_code = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    delivery_location = Column(String, nullable=True)
    delivery_note = Column(String, nullable=True)
    tracking_number = Column(String, unique=True, nullable=True)
    selected_partner_id = Column(Integer, nullable=True)
    selected_service_area_id = Column(Integer, nullable=True)
    estimated_delivery_min = Column(Integer, nullable=True)
    estimated_delivery_max = Column(Integer, nullable=True)
    payment_gateway_code = Column(String, nullable=True)
    payment_gateway_fee_amount = Column(Numeric(10, 2), nullable=True)
    payment_customer_total_amount = Column(Numeric(10, 2), nullable=True)
    payment_gateway_fee_passed_to_customer = Column(Numeric(10, 2), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    invoice_id = Column(Integer, ForeignKey("finance.ar_invoices.id"), nullable=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    user = relationship("User", foreign_keys=[user_id])
    customer = relationship("User", foreign_keys=[customer_id])
    items = relationship("OrderItem", back_populates="order")
    shipments = relationship("Shipment", back_populates="order")
    country = relationship("CountryConfig", foreign_keys=[country_code])
    invoice = relationship("ARInvoice", foreign_keys=[invoice_id], overlaps="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_product_id", "product_id"), {"schema": "commerce"})
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False)
    variant_id = Column(Integer, nullable=True)
    supplier_id = Column(Integer, nullable=True)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10, 2))
    price = Column(Numeric(10, 2))
    total_price = Column(Numeric(10, 2))
    product_name = Column(String, nullable=True)
    product_image = Column(String, nullable=True)
    selected_size = Column(String, nullable=True)
    selected_color = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    country = relationship("CountryConfig", foreign_keys=[country_code])
    order = relationship("Order", back_populates="items")
    product = relationship("Product", foreign_keys=[product_id])


class OrderLogisticsAllocation(Base):
    __tablename__ = "order_logistics_allocations"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id"), nullable=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=True)
    service_area_id = Column(Integer, ForeignKey("logistics.logistics_partner_service_areas.id"), nullable=True)
    allocation_source = Column(String, nullable=True)
    partner_name_snapshot = Column(String, nullable=True)
    partner_code_snapshot = Column(String, nullable=True)
    service_area_label_snapshot = Column(String, nullable=True)
    destination_country = Column(String, nullable=True)
    destination_city = Column(String, nullable=True)
    shipping_amount = Column(Numeric(10, 2), nullable=True)
    pickup_charge = Column(Numeric(10, 2), nullable=True)
    dropoff_charge = Column(Numeric(10, 2), nullable=True)
    accepted_vehicle_rule_id = Column(Integer, nullable=True)
    accepted_vehicle_type = Column(String, nullable=True)
    accepted_vehicle_multiplier = Column(Numeric(5, 4), nullable=True)
    accepted_shipping_amount = Column(Numeric(10, 2), nullable=True)
    accepted_pickup_charge = Column(Numeric(10, 2), nullable=True)
    accepted_dropoff_charge = Column(Numeric(10, 2), nullable=True)
    estimated_delivery_min = Column(Integer, nullable=True)
    estimated_delivery_max = Column(Integer, nullable=True)
    currency = Column(String, default="USD")
    pricing_breakdown_json = Column(Text, nullable=True)
    accepted_pricing_breakdown_json = Column(Text, nullable=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country = relationship("CountryConfig", foreign_keys=[country_code])


class ReturnRequest(Base):
    __tablename__ = "return_requests"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=False)
    order_item_id = Column(Integer, nullable=True)
    customer_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    user_id = synonym("customer_id")
    intent = Column(String, default="return")
    reason = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    supplier_review_state = Column(Text, nullable=True)
    images = Column(Text, nullable=True)
    status = Column(String, default="requested")
    refund_amount = Column(Numeric(10, 2), nullable=True)
    items = Column(Text, nullable=True)
    return_window_days = Column(Integer, default=10)
    delivered_at = Column(DateTime, nullable=True)
    return_deadline = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country = relationship("CountryConfig", foreign_keys=[country_code])
    order = relationship("Order")


class OrderNotification(Base):
    __tablename__ = "order_notifications"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)
    is_read = Column(Boolean, default=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")
    order = relationship("Order")
