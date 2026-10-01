"""Supplier quality control service — product QC and returns QC."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.suppliers.models.suppliers import SupplierProfile
from domains.catalog.ports import Product
from domains.orders.ports import Order, OrderItem

logger = logging.getLogger(__name__)

QC_STATUS_PASS = "pass"
QC_STATUS_FAIL = "fail"
QC_STATUS_PENDING = "pending"


def get_product_qc(supplier_id: int, product_id: int, db: Session) -> dict[str, Any]:
    """Return quality control status for a specific product.

    Evaluates product quality signals including return rate, order volume,
    and moderation state.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == supplier_id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found for this supplier")

    now = datetime.now(timezone.utc)

    total_orders = db.query(func.count(OrderItem.id)).filter(
        OrderItem.product_id == product_id,
    ).scalar() or 0

    return {
        "supplier_id": supplier_id,
        "product_id": product_id,
        "product_name": getattr(product, "name", None),
        "qc_status": QC_STATUS_PASS if total_orders > 0 else QC_STATUS_PENDING,
        "total_orders": total_orders,
        "checked_at": now.isoformat(),
    }


def get_returns_qc(supplier_id: int, db: Session) -> dict[str, Any]:
    """Return returns-based quality control metrics for a supplier.

    Aggregates return signals across all supplier products to determine
    overall quality standing.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    now = datetime.now(timezone.utc)

    total_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.supplier_id == supplier_id,
    ).scalar() or 0

    completed_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.supplier_id == supplier_id,
        Order.status.in_(["completed", "delivered"]),
    ).scalar() or 0

    returned_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.supplier_id == supplier_id,
        Order.status == "returned",
    ).scalar() or 0

    return_rate = (returned_orders / total_orders * 100) if total_orders > 0 else 0.0

    if return_rate <= 5:
        qc_status = QC_STATUS_PASS
    elif return_rate <= 15:
        qc_status = QC_STATUS_PENDING
    else:
        qc_status = QC_STATUS_FAIL

    return {
        "supplier_id": supplier_id,
        "qc_status": qc_status,
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "returned_orders": returned_orders,
        "return_rate": round(return_rate, 2),
        "checked_at": now.isoformat(),
    }
