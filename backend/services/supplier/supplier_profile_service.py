"""Supplier profile service.

Owns all DB work behind ``routers/supplier/supplier_profile.py`` so the router
stays a thin delegator (layering: LC1/W1).

These helpers previously lived in ``services/supplier/supplier_read_service.py``,
which is documented as read-only; ``create_supplier_profile`` and
``update_supplier_profile`` perform writes, so they belong here. That module
re-exports them for backward compatibility.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import SupplierProfile
from data.services_write_helpers import (
    add_and_flush,
    commit_only,
    refresh_only,
)
from utils.slug import generate_slug


def get_supplier_profile_by_user(db: Session, user_id: int) -> SupplierProfile:
    """Return the supplier profile owned by ``user_id`` (404 if absent)."""
    profile = (
        db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    )
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile


def create_supplier_profile(db: Session, user, payload) -> SupplierProfile:
    """Create a supplier profile, preserving slug generation and role flip."""
    if (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == user.id)
        .first()
    ):
        raise HTTPException(400, "Profile already exists")
    profile = SupplierProfile(
        user_id=user.id,
        slug=generate_slug(payload.business_name),
        **payload.model_dump(),
    )
    add_and_flush(db, profile)
    commit_only(db)
    refresh_only(db, profile)
    user.role = "supplier"
    commit_only(db)
    return profile


def update_supplier_profile(db: Session, user, payload) -> SupplierProfile:
    """Update the supplier profile owned by ``user``."""
    profile = get_supplier_profile_by_user(db, user.id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(profile, k, v)
    commit_only(db)
    refresh_only(db, profile)
    return profile
