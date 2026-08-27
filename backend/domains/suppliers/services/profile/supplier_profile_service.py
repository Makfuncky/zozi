"""Auto-migrated service logic from routers/supplier_profile.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import SupplierProfileCreate, SupplierProfileOut, SupplierProfileUpdate

from domains.governance.models.user import User
from domains.comms.models.suppliers import SupplierProfile

from infrastructure.utils.dependencies import get_current_user, require_supplier

from infrastructure.utils.slug import generate_slug

def get_supplier_profile(current_user: User, db: Session):
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not profile: raise HTTPException(404, "Profile not found")
    return profile

def create_supplier_profile(payload: SupplierProfileCreate, current_user: User, db: Session):
    if db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first():
        raise HTTPException(400, "Profile already exists")
    profile = SupplierProfile(user_id=current_user.id, slug=generate_slug(payload.business_name), **payload.model_dump())
    db.add(profile); db.commit(); db.refresh(profile)
    current_user.role = "supplier"; db.commit()
    return profile

def update_supplier_profile(payload: SupplierProfileUpdate, current_user: User, db: Session):
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not profile: raise HTTPException(404)
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(profile, k, v)
    db.commit(); db.refresh(profile)
    return profile


def get_supplier_profile(db: Session, user_id: int):
    """Sanctioned cross-domain read: fetch supplier profile by user id."""
    from domains.catalog.services.products.products_service import get_supplier_profile as _svc
    return _svc(db, user_id)


