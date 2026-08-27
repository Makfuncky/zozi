"""Supplier analytics service — aggregates supplier performance data."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.catalog.models.products import Product
from domains.comms.models.suppliers import SupplierProfile
from domains.orders.models.orders import Order, OrderItem

logger = logging.getLogger(__name__)


def get_supplier_analytics_summary(current_user: Any, db: Session) -> dict:
    """Return aggregated analytics summary for the authenticated supplier."""
    user_id = current_user.id if hasattr(current_user, "id") else current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user session")

    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    total_products = db.query(Product).filter(
        Product.supplier_id == supplier.id,
        Product.is_deleted == False,
    ).count()

    total_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.supplier_id == supplier.id,
    ).scalar() or 0

    total_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).filter(
        OrderItem.supplier_id == supplier.id,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    recent_revenue = db.query(
        func.sum(OrderItem.price * OrderItem.quantity)
    ).join(Order).filter(
        OrderItem.supplier_id == supplier.id,
        Order.created_at >= thirty_days_ago,
        Order.status.in_(["completed", "shipped", "delivered"]),
    ).scalar() or 0

    avg_order_value = float(total_revenue / total_orders) if total_orders > 0 else 0

    return {
        "overview": {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "recent_revenue_30d": float(recent_revenue),
            "average_order_value": float(avg_order_value),
        },
        "period": "all_time",
        "generated_at": now.isoformat(),
    }
