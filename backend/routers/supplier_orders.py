"""Supplier orders sub-router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Order, OrderItem, SupplierProfile, User
from utils.dependencies import require_supplier

router = APIRouter()

@router.get("")
def list_supplier_orders(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404)
    orders = db.query(Order).join(OrderItem).filter(OrderItem.supplier_id == supplier.id).distinct().all()
    return orders

