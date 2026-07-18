"""Supplier products sub-router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Product, SupplierProfile, User
from db.schemas import ProductOut, ProductCreate, ProductUpdate
from utils.dependencies import require_supplier
import math

router = APIRouter()

@router.get("")
def list_my_products(page: int = Query(1, ge=1), size: int = Query(20), current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    q = db.query(Product).filter(Product.supplier_id == supplier.id)
    total = q.count()
    items = q.offset((page-1)*size).limit(size).all()
    return {"items": items, "total": total, "page": page, "size": size, "pages": math.ceil(total/size) if total else 1}

