"""Supplier profile router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models import SupplierProfile, User
from db.schemas import SupplierProfileCreate, SupplierProfileOut, SupplierProfileUpdate
from utils.dependencies import get_current_user, require_supplier
from utils.slug import generate_slug

from services.write_helpers import add_and_flush, commit_only, refresh_only
router = APIRouter()

@router.get("/profile", response_model=SupplierProfileOut)
def get_supplier_profile(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not profile: raise HTTPException(404, "Profile not found")
    return profile

@router.post("/profile", response_model=SupplierProfileOut, status_code=201)
def create_supplier_profile(payload: SupplierProfileCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first():
        raise HTTPException(400, "Profile already exists")
    profile = SupplierProfile(user_id=current_user.id, slug=generate_slug(payload.business_name), **payload.model_dump())
    add_and_flush(db, profile); commit_only(db); refresh_only(db, profile)
    current_user.role = "supplier"; commit_only(db)
    return profile

@router.put("/profile", response_model=SupplierProfileOut)
def update_supplier_profile(payload: SupplierProfileUpdate, current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not profile: raise HTTPException(404)
    for k, v in payload.model_dump(exclude_unset=True).items(): setattr(profile, k, v)
    commit_only(db); refresh_only(db, profile)
    return profile

