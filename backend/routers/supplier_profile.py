"""Supplier profile router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import User
from data.schemas import SupplierProfileCreate, SupplierProfileOut, SupplierProfileUpdate
from utils.dependencies import get_current_user, require_supplier
from services.supplier.supplier_profile_service import (
    create_supplier_profile,
    get_supplier_profile_by_user,
    update_supplier_profile,
)

router = APIRouter()

@router.get("/profile", response_model=SupplierProfileOut)
def get_supplier_profile(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    return get_supplier_profile_by_user(db, current_user.id)

@router.post("/profile", response_model=SupplierProfileOut, status_code=201)
def create_supplier_profile_endpoint(payload: SupplierProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_supplier_profile(db, current_user, payload)

@router.put("/profile", response_model=SupplierProfileOut)
def update_supplier_profile_endpoint(payload: SupplierProfileUpdate, current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    return update_supplier_profile(db, current_user, payload)

