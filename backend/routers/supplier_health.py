"""
Supplier Health API Endpoints

Thin router: all DB work is delegated to
``services/supplier/supplier_health_service.py`` (reached through the exempt
``data`` circuit-layer shim), so this module never touches a SQLAlchemy session
directly (layering: LC1/W1).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from data.db import get_db
from data.dependencies_auth import get_current_user
from data.services_supplier_health_service import get_supplier_health, list_supplier_health

router = APIRouter()


@router.get("/health/suppliers/{supplier_id}")
def get_supplier_health_endpoint(
    supplier_id: int,
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_supplier_health(db, supplier_id, country_code, current_user)


@router.get("/health/suppliers")
def list_supplier_health_endpoint(
    country_code: str = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_supplier_health(db, country_code, skip, limit, current_user)
