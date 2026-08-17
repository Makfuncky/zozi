"""Auto-migrated service logic from routers/supplier_profile_create.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from models import User

from infrastructure.database.schemas import SupplierProfileCreate, SupplierProfileOut, SupplierProfileUpdate

from infrastructure.utils.dependencies import get_current_user, require_supplier

from services.supplier.supplier_profile_write_service import (
    create_supplier_profile,
    get_supplier_profile,
    update_supplier_profile,
)

def get_supplier_profile_route(current_user: User, db: Session):
    return get_supplier_profile(current_user, db)

def create_supplier_profile_route(payload: SupplierProfileCreate, current_user: User, db: Session):
    return create_supplier_profile(current_user, payload, db)

def update_supplier_profile_route(payload: SupplierProfileUpdate, current_user: User, db: Session):
    profile = update_supplier_profile(current_user, payload, db)
    if profile is None:
        raise HTTPException(404, "Profile not found")
    return profile


