"""Supplier payouts sub-router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import Payout, SupplierProfile, User
from db.schemas import PayoutOut
from utils.dependencies import require_supplier

router = APIRouter()

@router.get("", response_model=list[PayoutOut])
def list_payouts(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404)
    return db.query(Payout).filter(Payout.supplier_id == supplier.id).order_by(Payout.created_at.desc()).all()

