"""Supplier analytics sub-router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.database import get_db
from models import Order, OrderItem, Product, SupplierProfile, User
from utils.dependencies import require_supplier

router = APIRouter()

@router.get("/summary")
def analytics_summary(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404)
    total_products = db.query(func.count(Product.id)).filter(Product.supplier_id == supplier.id).scalar()
    total_sales = db.query(func.coalesce(func.sum(OrderItem.total_price), 0)).filter(OrderItem.supplier_id == supplier.id).scalar()
    total_orders = db.query(func.count(func.distinct(OrderItem.order_id))).filter(OrderItem.supplier_id == supplier.id).scalar()
    return {"total_products": total_products, "total_sales": float(total_sales), "total_orders": total_orders}

