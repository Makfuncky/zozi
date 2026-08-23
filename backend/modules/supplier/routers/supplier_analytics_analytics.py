"""Supplier analytics sub-router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.utils.dependencies import require_supplier
from domains.suppliers.services.supplier_analytics_service import get_supplier_analytics_summary

router = APIRouter(prefix="/api/v1/supplier")

@router.get("/summary")
def analytics_summary(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    return get_supplier_analytics_summary(db, current_user)

