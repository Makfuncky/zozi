"""Supplier analytics router — consolidated from 2 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/supplier/analytics", tags=["supplier", "analytics"])


# === From supplier_analytics.py ===
"""Supplier analytics sub-router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.catalog.models.products import Product
from domains.suppliers.models.suppliers import SupplierProfile
from domains.orders.models.order_entities import OrderItem
from infrastructure.utils.dependencies import require_supplier


@router.get("/summary")
def analytics_summary(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404)
    total_products = db.query(func.count(Product.id)).filter(Product.supplier_id == supplier.id).scalar()
    total_sales = db.query(func.coalesce(func.sum(OrderItem.total_price), 0)).filter(OrderItem.supplier_id == supplier.id).scalar()
    total_orders = db.query(func.count(func.distinct(OrderItem.order_id))).filter(OrderItem.supplier_id == supplier.id).scalar()
    return {"total_products": total_products, "total_sales": float(total_sales), "total_orders": total_orders}


# === From supplier_analytics_analytics.py ===
"""Supplier analytics sub-router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.utils.dependencies import require_supplier
from domains.suppliers.services._auto_stubs import get_supplier_analytics_summary


@router.get("/summary")
def analytics_summary(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    return get_supplier_analytics_summary(db, current_user)


