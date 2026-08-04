"""Service methods for supplier write operations."""
from __future__ import annotations
from sqlalchemy.orm import Session
from data.models import SupplierProfile
from services.core.users_write_service import get_user_by_id


def get_supplier_profile_by_id(db: Session, profile_id: int) -> SupplierProfile | None:
    """Get a supplier profile by ID."""
    return db.query(SupplierProfile).filter(SupplierProfile.id == profile_id).first()


def list_supplier_profiles(db: Session) -> list[SupplierProfile]:
    """List all supplier profiles."""
    return db.query(SupplierProfile).all()


def get_supplier_stats(db: Session) -> dict:
    """Get supplier statistics."""
    q = (
        db.query(SupplierProfile.verification_status, SupplierProfile.is_active)
        .all()
    )
    pending = sum(1 for row in q if row[0] == "pending")
    active = sum(1 for row in q if row[1] is True)
    suspended = sum(1 for row in q if row[1] is False)
    return {"pending": pending, "active": active, "suspended": suspended}


def get_supplier_profile_by_user_id(db: Session, user_id: int) -> SupplierProfile | None:
    """Get supplier profile by user ID."""
    return db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()


def create_supplier_profile(db: Session, **kwargs) -> SupplierProfile:
    """Create a supplier profile."""
    profile = SupplierProfile(**kwargs)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_supplier_profile(db: Session, profile_id: int, **kwargs) -> SupplierProfile | None:
    """Update a supplier profile."""
    profile = get_supplier_profile_by_id(db, profile_id)
    if not profile:
        return None
    for key, value in kwargs.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


def save_supplier_profile(db: Session, profile: SupplierProfile) -> SupplierProfile:
    """Commit and refresh a mutated supplier profile."""
    db.commit()
    db.refresh(profile)
    return profile


def commit_supplier_changes(db: Session) -> None:
    """Commit pending supplier-related changes."""
    db.commit()
