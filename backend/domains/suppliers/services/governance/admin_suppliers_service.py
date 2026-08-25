"""Admin supplier management service.

Consolidates admin_suppliers_service.py (admin supplier CRUD),
admin_suppliers_read_service.py (read helpers), and
admin_supplier_review_service.py (review & configuration).
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Path, Query

from sqlalchemy.orm import Session

from modules.admin.routers.admin_controller import (
    archive_entity,
    hard_delete_entity,
    restore_entity,
)

from infrastructure.database.database import get_db

from infrastructure.database.schemas import ArchiveRequest

from domains.governance.models.user import User
from domains.comms.models.suppliers import SupplierProfile

from domains.country.utils.country_rls import enforce_country_access

from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.pagination import paginated_response
from infrastructure.utils.pagination import keyset_offset_window


# ── Read Helpers (merged from admin_suppliers_read_service.py) ────────────────

def _supplier_to_dict(s) -> dict:
    return {
        "id": s.id,
        "user_id": s.user_id,
        "business_name": s.business_name,
        "slug": s.slug,
        "business_type": s.business_type,
        "country_code": s.country_code,
        "phone_business": s.phone_business,
        "website": s.website,
        "address": s.address,
        "city": s.city,
        "region": s.region,
        "verification_status": s.verification_status,
        "verified_at": s.verified_at.isoformat() if s.verified_at else None,
        "is_active": s.is_active,
        "is_deleted": getattr(s, "is_deleted", False),
        "badge_level": getattr(s, "badge_level", None),
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def list_suppliers_by_country(code, include_deleted, q, page, page_size, status, db: Session):
    enforce_country_access(code, db=db)
    query = db.query(SupplierProfile)
    if code != "*":
        query = query.filter(SupplierProfile.country_code == code.upper())
    if not include_deleted:
        query = query.filter(SupplierProfile.is_deleted == False)
    if q:
        query = query.filter(SupplierProfile.business_name.ilike(f"%{q}%"))
    if status:
        query = query.filter(SupplierProfile.verification_status == status)
    total = query.count()
    items = keyset_offset_window(query, offset=(page - 1) * page_size, limit=page_size)
    return {
        "items": [_supplier_to_dict(s) for s in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": {
            "pending_suppliers": db.query(SupplierProfile).filter(
                SupplierProfile.verification_status == "pending",
                *([] if code == "*" else [SupplierProfile.country_code == code.upper()])
            ).count(),
            "active_suppliers": db.query(SupplierProfile).filter(
                SupplierProfile.is_active == True,
                *([] if code == "*" else [SupplierProfile.country_code == code.upper()])
            ).count(),
            "suspended_suppliers": db.query(SupplierProfile).filter(
                SupplierProfile.is_active == False,
                *([] if code == "*" else [SupplierProfile.country_code == code.upper()])
            ).count(),
        },
    }


def list_pending_kyc_suppliers(code, page, size, db: Session):
    enforce_country_access(code, db=db)
    q = db.query(SupplierProfile).filter(
        SupplierProfile.verification_status.in_(["pending", "documents_submitted", "under_review"]),
        SupplierProfile.is_deleted == False,
    )
    if code != "*":
        q = q.filter(SupplierProfile.country_code == code.upper())
    return paginated_response(
        q.order_by(SupplierProfile.updated_at.desc()),
        page=page,
        size=size,
        serializer=_supplier_to_dict,
    )


def get_supplier_by_country(code, supplier_id, db: Session):
    enforce_country_access(code, db=db)
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    if code != "*" and s.country_code and s.country_code.upper() != code.upper():
        raise HTTPException(403, detail="Supplier does not belong to this country")
    return _supplier_to_dict(s)


def list_suppliers_global(include_deleted, db: Session):
    q = db.query(SupplierProfile)
    if not include_deleted:
        q = q.filter(SupplierProfile.is_deleted == False)
    return [_supplier_to_dict(s) for s in q.all()]


def list_all_suppliers(include_deleted, country, status, q, page, page_size, db: Session):
    query = db.query(SupplierProfile)
    if not include_deleted:
        query = query.filter(SupplierProfile.is_deleted == False)
    if country and country != "*":
        query = query.filter(SupplierProfile.country_code == country.upper())
    if status:
        query = query.filter(SupplierProfile.verification_status == status)
    if q:
        query = query.filter(SupplierProfile.business_name.ilike(f"%{q}%"))
    total = query.count()
    items = keyset_offset_window(query, offset=(page - 1) * page_size, limit=page_size)
    return {
        "items": [_supplier_to_dict(s) for s in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": {
            "pending_suppliers": db.query(SupplierProfile).filter(SupplierProfile.verification_status == "pending").count(),
            "active_suppliers": db.query(SupplierProfile).filter(SupplierProfile.is_active == True).count(),
            "suspended_suppliers": db.query(SupplierProfile).filter(SupplierProfile.is_active == False).count(),
            "total_revenue": 0,
        },
    }


def list_all_suppliers_frontend(include_deleted, country, status, q, page, page_size, db: Session):
    query = db.query(SupplierProfile)
    if not include_deleted:
        query = query.filter(SupplierProfile.is_deleted == False)
    if country and country != "*":
        query = query.filter(SupplierProfile.country_code == country.upper())
    if status:
        query = query.filter(SupplierProfile.verification_status == status)
    if q:
        query = query.filter(SupplierProfile.business_name.ilike(f"%{q}%"))
    total = query.count()
    items = keyset_offset_window(query, offset=(page - 1) * page_size, limit=page_size)
    return {
        "items": [_supplier_to_dict(s) for s in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": {
            "pending_suppliers": db.query(SupplierProfile).filter(SupplierProfile.verification_status == "pending").count(),
            "active_suppliers": db.query(SupplierProfile).filter(SupplierProfile.is_active == True).count(),
            "suspended_suppliers": db.query(SupplierProfile).filter(SupplierProfile.is_active == False).count(),
            "total_revenue": 0,
        },
    }


def supplier_comparison_frontend(db: Session):
    rows = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.is_deleted == False)
        .order_by(SupplierProfile.id.asc())
        .limit(200)
        .all()
    )
    data = [
        {
            "id": s.id,
            "business_name": s.business_name,
            "country_code": s.country_code,
            "verification_status": s.verification_status,
            "badge_level": getattr(s, "badge_level", None),
            "is_active": s.is_active,
            "revenue": 0,
            "order_count": getattr(s, "order_count", 0),
            "product_count": getattr(s, "product_count", 0),
        }
        for s in rows
    ]
    return {"data": data, "total": len(data), "page": 1, "page_size": len(data) or 1}


# ── Admin Supplier Review & Configuration (merged from admin_supplier_review_service.py) ──

def _summarize(db: Session, code: Optional[str]) -> dict:
    if code == "*":
        return {
            "pending_suppliers": db.query(SupplierProfile).filter(
                SupplierProfile.verification_status == "pending"
            ).count(),
            "active_suppliers": db.query(SupplierProfile).filter(
                SupplierProfile.is_active == True
            ).count(),
            "suspended_suppliers": db.query(SupplierProfile).filter(
                SupplierProfile.is_active == False
            ).count(),
        }
    cc = code.upper() if code else None
    return {
        "pending_suppliers": db.query(SupplierProfile).filter(
            SupplierProfile.verification_status == "pending",
            SupplierProfile.country_code == cc,
        ).count(),
        "active_suppliers": db.query(SupplierProfile).filter(
            SupplierProfile.is_active == True,
            SupplierProfile.country_code == cc,
        ).count(),
        "suspended_suppliers": db.query(SupplierProfile).filter(
            SupplierProfile.is_active == False,
            SupplierProfile.country_code == cc,
        ).count(),
    }


def _get_owned_supplier(db: Session, code: str, supplier_id: int) -> SupplierProfile:
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    if code != "*" and s.country_code and s.country_code.upper() != code.upper():
        raise HTTPException(403, detail="Supplier does not belong to this country")
    return s


def update_supplier_by_country(
    db: Session, code: str, supplier_id: int,
    business_name: Optional[str], verification_status: Optional[str], badge_level: Optional[str],
) -> dict:
    s = _get_owned_supplier(db, code, supplier_id)
    if business_name is not None:
        s.business_name = business_name
    if verification_status is not None:
        s.verification_status = verification_status
    if badge_level is not None and hasattr(s, "badge_level"):
        s.badge_level = badge_level
    db.commit()
    db.refresh(s)
    return _supplier_to_dict(s)


def approve_supplier_kyc_review(db: Session, code: str, supplier_id: int, admin_id: int) -> dict:
    s = _get_owned_supplier(db, code, supplier_id)
    s.verification_status = "approved"
    from infrastructure.utils.datetime_utils import utcnow
    s.verified_at = utcnow()
    s.verified_by = admin_id if hasattr(s, "verified_by") else None
    db.commit()
    return {"message": "Supplier KYC approved"}


def reject_supplier_kyc_review(db: Session, code: str, supplier_id: int, reason: Optional[str]) -> dict:
    s = _get_owned_supplier(db, code, supplier_id)
    s.verification_status = "rejected"
    if hasattr(s, "verification_note"):
        s.verification_note = reason
    db.commit()
    return {"message": "Supplier KYC rejected", "reason": reason}


def _set_user_active(db: Session, supplier: SupplierProfile, is_active: int) -> None:
    if supplier.user_id:
        u = db.query(User).filter(User.id == supplier.user_id).first()
        if u:
            u.is_active = is_active


def suspend_supplier_review(db: Session, supplier_id: int) -> dict:
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    s.is_active = False
    _set_user_active(db, s, 0)
    db.commit()
    return {"message": "Supplier suspended"}


def activate_supplier_review(db: Session, supplier_id: int) -> dict:
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    s.is_active = True
    _set_user_active(db, s, 1)
    db.commit()
    return {"message": "Supplier activated"}


def bulk_supplier_action_review(db: Session, payload: dict) -> dict:
    ids = payload.get("supplier_ids") or []
    action = (payload.get("action") or "").lower()
    badge_level = payload.get("badge_level")
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=422, detail="supplier_ids is required")

    processed = 0
    for sid in ids:
        s = db.query(SupplierProfile).filter(SupplierProfile.id == sid).first()
        if not s:
            continue
        if action == "verify":
            s.verification_status = "approved"
            from infrastructure.utils.datetime_utils import utcnow
            if hasattr(s, "verified_at"):
                s.verified_at = utcnow()
        elif action == "reject":
            s.verification_status = "rejected"
        elif action == "suspend":
            s.is_active = False
            _set_user_active(db, s, 0)
        elif action == "activate":
            s.is_active = True
            _set_user_active(db, s, 1)
        elif action == "delete":
            if hasattr(s, "is_deleted"):
                s.is_deleted = True
            s.is_active = False
        elif action == "badge":
            if badge_level is not None and hasattr(s, "badge_level"):
                s.badge_level = badge_level
        processed += 1
    db.commit()
    return {"processed": processed, "action": action}


def bulk_restore_suppliers_review(db: Session, payload: dict) -> dict:
    ids = payload.get("supplier_ids") or []
    if not isinstance(ids, list) or not ids:
        raise HTTPException(status_code=422, detail="supplier_ids is required")
    processed = 0
    for sid in ids:
        s = db.query(SupplierProfile).filter(SupplierProfile.id == sid).first()
        if not s:
            continue
        if hasattr(s, "is_deleted"):
            s.is_deleted = False
        s.is_active = True
        processed += 1
    db.commit()
    return {"processed": processed}


def restore_supplier_frontend_review(db: Session, supplier_id: int) -> dict:
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    if hasattr(s, "is_deleted"):
        s.is_deleted = False
    s.is_active = True
    db.commit()
    return {"message": "Supplier restored", "id": supplier_id}


def refresh_supplier_badge_review(db: Session, supplier_id: int) -> dict:
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    if not hasattr(s, "badge_level"):
        raise HTTPException(status_code=400, detail="Supplier does not support badge levels")
    return {"id": s.id, "badge_level": s.badge_level}
