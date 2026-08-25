"""Suppliers domain — sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain reads may ONLY happen through a
publishing domain's ports.py. Other domains import these functions instead of
importing domains.suppliers.models or domains.suppliers.services directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via rbac).

This file mirrors the domain-level ``domains/suppliers/ports.py`` surface so that
service-layer consumers can import from the canonical services path.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from .events import SuppliersEvent  # noqa: F401 — re-export for type hints


def _get_models():
    from domains.suppliers.models.suppliers import SupplierProfile
    return (SupplierProfile,)


def get_supplier_profile_by_user(db: Session, user_id: int) -> Optional[object]:
    """Return the supplier profile for a user, or None if not found.

    Sanctioned cross-domain read: other domains call this instead of querying
    the supplier tables directly.
    """
    (SupplierProfile,) = _get_models()
    return (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == user_id)
        .first()
    )


def get_supplier_profile_by_id(db: Session, profile_id: int) -> Optional[object]:
    """Return a supplier profile by its primary key, or None if not found."""
    (SupplierProfile,) = _get_models()
    return db.query(SupplierProfile).filter(SupplierProfile.id == profile_id).first()


__all__ = [
    "get_supplier_profile_by_user",
    "get_supplier_profile_by_id",
]
