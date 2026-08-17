"""Supplier analytics read operations.

Owns the DB reads for supplier analytics summary. Routers must not query the
session directly for this operation.
"""
from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import OrderItem, Product
from services.supplier.supplier_profile_write_service import get_supplier_profile
import structlog
logger = structlog.get_logger(__name__)


def get_supplier_analytics_summary(db: Session, current_user) -> dict:
    """Compute product/sales/order totals for the requesting supplier."""
    supplier = get_supplier_profile(current_user, db)
    total_products = db.query(func.count(Product.id)).filter(Product.supplier_id == supplier.id).scalar()
    total_sales = db.query(func.coalesce(func.sum(OrderItem.total_price), 0)).filter(
        OrderItem.supplier_id == supplier.id
    ).scalar()
    total_orders = db.query(func.count(func.distinct(OrderItem.order_id))).filter(
        OrderItem.supplier_id == supplier.id
    ).scalar()
    return {
        "total_products": total_products,
        "total_sales": float(total_sales),
        "total_orders": total_orders,
    }
