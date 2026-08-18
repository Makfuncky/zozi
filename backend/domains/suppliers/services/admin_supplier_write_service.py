"""Write-side service for the admin supplier surface.

W1 contract: only ``services/**`` may own DB transactions. Every mutation that
used to live inside ``routers/admin_suppliers.py`` (profile patch, KYC
approve/reject, suspend/activate, bulk actions and restores) is implemented
here, preserving the original semantics and ``HTTPException`` behaviour.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.accounts.models.user import User
from domains.comms.models.suppliers import SupplierProfile
from infrastructure.utils.datetime_utils import utcnow
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "update_supplier_profile",
    "approve_supplier_kyc",
    "reject_supplier_kyc",
    "suspend_supplier",
    "activate_supplier",
    "bulk_supplier_action",
    "bulk_restore_suppliers",
    "restore_supplier",
]


def _get_supplier_or_404(db: Session, supplier_id: int) -> SupplierProfile:
    supplier = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.id == supplier_id)
        .first()
    )
    if not supplier:
        raise HTTPException(404, detail="Supplier not found")
    return supplier


def _assert_country_match(supplier: SupplierProfile, code: str) -> None:
    if code != "*" and supplier.country_code and supplier.country_code.upper() != code.upper():
        raise HTTPException(403, detail="Supplier does not belong to this country")


def update_supplier_profile(
    db: Session,
    code: str,
    supplier_id: int,
    business_name: Optional[str] = None,
    verification_status: Optional[str] = None,
    badge_level: Optional[str] = None,
) -> SupplierProfile:
    """Patch a country-scoped supplier profile. Returns the refreshed ORM row."""
    supplier = _get_supplier_or_404(db, supplier_id)
    _assert_country_match(supplier, code)
    if business_name is not None:
        supplier.business_name = business_name
    if verification_status is not None:
        supplier.verification_status = verification_status
    if badge_level is not None and hasattr(supplier, "badge_level"):
        supplier.badge_level = badge_level
    db.commit()
    db.refresh(supplier)
    return supplier


def approve_supplier_kyc(db: Session, code: str, supplier_id: int, admin_id: Any) -> dict:
    """Mark a supplier's KYC as approved."""
    supplier = _get_supplier_or_404(db, supplier_id)
    supplier.verification_status = "approved"
    supplier.verified_at = utcnow()
    supplier.verified_by = admin_id if hasattr(supplier, "verified_by") else None
    db.commit()
    return {"message": "Supplier KYC approved"}


def reject_supplier_kyc(
    db: Session,
    code: str,
    supplier_id: int,
    reason: Optional[str] = None,
) -> dict:
    """Mark a supplier's KYC as rejected."""
    supplier = _get_supplier_or_404(db, supplier_id)
    supplier.verification_status = "rejected"
    if hasattr(supplier, "verification_note"):
        supplier.verification_note = reason
    db.commit()
    return {"message": "Supplier KYC rejected", "reason": reason}


def suspend_supplier(db: Session, code: str, supplier_id: int) -> dict:
    """Deactivate the login account backing a supplier profile."""
    supplier = _get_supplier_or_404(db, supplier_id)
    user = db.query(User).filter(User.id == supplier.user_id).first()
    if user:
        user.is_active = 0
    db.commit()
    return {"message": "Supplier suspended"}


def activate_supplier(db: Session, code: str, supplier_id: int) -> dict:
    """Reactivate the login account backing a supplier profile."""
    supplier = _get_supplier_or_404(db, supplier_id)
    user = db.query(User).filter(User.id == supplier.user_id).first()
    if user:
        user.is_active = 1
    db.commit()
    return {"message": "Supplier activated"}


def bulk_supplier_action(db: Session, payload: dict) -> dict:
    """Apply verify/reject/suspend/activate/delete/badge across many suppliers."""
    ids = payload.get("supplier_ids") or []
    action = (payload.get("action") or "").lower()
    badge_level = payload.get("badge_level")
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=422, detail="supplier_ids is required")

    processed = 0
    suppliers_map = {
        s.id: s
        for s in db.query(SupplierProfile).filter(SupplierProfile.id.in_(ids)).all()
    }
    user_ids = [s.user_id for s in suppliers_map.values() if s.user_id]
    user_map: Dict[int, Any] = {}
    if user_ids:
        user_map = {
            u.id: u
            for u in db.query(User).filter(User.id.in_(user_ids)).all()
        }
    for sid in ids:
        supplier = suppliers_map.get(sid)
        if not supplier:
            continue
        if action == "verify":
            supplier.verification_status = "approved"
            if hasattr(supplier, "verified_at"):
                supplier.verified_at = utcnow()
        elif action == "reject":
            supplier.verification_status = "rejected"
        elif action == "suspend":
            supplier.is_active = False
            if supplier.user_id:
                account = user_map.get(supplier.user_id)
                if account:
                    account.is_active = 0
        elif action == "activate":
            supplier.is_active = True
            if supplier.user_id:
                account = user_map.get(supplier.user_id)
                if account:
                    account.is_active = 1
        elif action == "delete":
            if hasattr(supplier, "is_deleted"):
                supplier.is_deleted = True
            supplier.is_active = False
        elif action == "badge":
            if badge_level is not None and hasattr(supplier, "badge_level"):
                supplier.badge_level = badge_level
        processed += 1
    db.commit()
    return {"processed": processed, "action": action}


def bulk_restore_suppliers(db: Session, payload: dict) -> dict:
    """Undelete and reactivate a batch of supplier profiles."""
    ids = payload.get("supplier_ids") or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=422, detail="supplier_ids is required")
    processed = 0
    suppliers_map = {
        s.id: s
        for s in db.query(SupplierProfile).filter(SupplierProfile.id.in_(ids)).all()
    }
    user_ids = [s.user_id for s in suppliers_map.values() if s.user_id]
    user_map: Dict[int, Any] = {}
    if user_ids:
        user_map = {
            u.id: u
            for u in db.query(User).filter(User.id.in_(user_ids)).all()
        }
    for sid in ids:
        supplier = suppliers_map.get(sid)
        if not supplier:
            continue
        if hasattr(supplier, "is_deleted"):
            supplier.is_deleted = False
        supplier.is_active = True
        if supplier.user_id:
            account = user_map.get(supplier.user_id)
            if account:
                account.is_active = 1
        processed += 1
    db.commit()
    return {"processed": processed}


def restore_supplier(db: Session, supplier_id: int) -> dict:
    """Undelete and reactivate a single supplier profile."""
    supplier = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.id == supplier_id)
        .first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if hasattr(supplier, "is_deleted"):
        supplier.is_deleted = False
    supplier.is_active = True
    if supplier.user_id:
        account = db.query(User).filter(User.id == supplier.user_id).first()
        if account:
            account.is_active = 1
    db.commit()
    return {"message": "Supplier restored", "id": supplier_id}
