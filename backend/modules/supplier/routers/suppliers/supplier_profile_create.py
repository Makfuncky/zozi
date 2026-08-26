# === From supplier_profile_create.py ===
from suppliers.router import router  # noqa: F401
"""Supplier profile router.

Thin HTTP layer: delegates all profile business logic to
``services.supplier.supplier_profile_write_service`` so the router stays free of
``db.add``/``db.commit``. Endpoint paths, auth and response models are unchanged.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.database.schemas import SupplierProfileCreate, SupplierProfileOut, SupplierProfileUpdate
from infrastructure.utils.dependencies import get_current_user, require_supplier
from domains.accounts.services.auth.auth_service import create_supplier_profile
from domains.catalog.services.products.products_service import get_supplier_profile
from domains.suppliers.services.health.supplier_health import update_supplier_profile


@router.get("/profile", response_model=SupplierProfileOut)
def get_supplier_profile_route(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    return get_supplier_profile(current_user, db)


@router.post("/profile", response_model=SupplierProfileOut, status_code=201)
def create_supplier_profile_route(payload: SupplierProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_supplier_profile(current_user, payload, db)


@router.put("/profile", response_model=SupplierProfileOut)
def update_supplier_profile_route(payload: SupplierProfileUpdate, current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    profile = update_supplier_profile(current_user, payload, db)
    if profile is None:
        raise HTTPException(404, "Profile not found")
    return profile

