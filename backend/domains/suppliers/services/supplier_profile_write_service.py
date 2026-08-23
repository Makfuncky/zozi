"""Supplier profile write service.

Owns DB writes for `backend/routers/supplier_profile.py` so the router stays
free of `db.add`/`db.commit` (W1). Functions are db-param.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.models.user import User
from domains.comms.models.suppliers import SupplierProfile
from infrastructure.utils.slug import generate_slug
import structlog
logger = structlog.get_logger(__name__)


def get_supplier_profile(current_user: User, db: Session) -> SupplierProfile:
    profile = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == current_user.id)
        .first()
    )
    if profile is None:
        raise HTTPException(404, "Profile not found")
    return profile


def create_supplier_profile(current_user: User, payload, db: Session) -> SupplierProfile:
    existing = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == current_user.id)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=400, detail="Profile already exists")
    profile = SupplierProfile(
        user_id=current_user.id,
        slug=generate_slug(payload.business_name),
        **payload.model_dump(),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    if getattr(current_user, "role", None) != "supplier":
        current_user.role = "supplier"
        db.commit()
    return profile


def update_supplier_profile(current_user: User, payload, db: Session) -> Optional[SupplierProfile]:
    profile = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == current_user.id)
        .first()
    )
    if profile is None:
        return None
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(profile, k, v)
    db.commit()
    db.refresh(profile)
    return profile
