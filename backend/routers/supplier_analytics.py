"""Supplier analytics sub-router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import User
from utils.dependencies import require_supplier
from services.supplier.supplier_read_service import get_supplier_analytics_summary

router = APIRouter()

@router.get("/summary")
def analytics_summary(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    return get_supplier_analytics_summary(db, current_user.id)

