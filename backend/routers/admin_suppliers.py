"""Admin suppliers router — country-scoped."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from data.db import get_db
from data.models import SupplierProfile, User
from data.schemas import ArchiveRequest, BulkActionRequest
from utils.dependencies import require_admin
from utils.country_rls import enforce_country_access
from utils.pagination import cursor_paginate_desc, build_cursor_pagination_payload
from data.controllers_admin_controller import (
    archive_entity,
    restore_entity,
    bulk_archive_entities,
    bulk_restore_entities,
    hard_delete_entity,
)
from services.write_helpers import commit_and_refresh, commit_only

router = APIRouter()


def _user_ctx(u: User) -> dict:
    return {"id": u.id, "username": u.username, "role": u.role}


# ── Country-scoped endpoints ──────────────────────────────────────────────────

@router.get("/{code}/suppliers")
def list_suppliers_by_country(
    code: str = Path(..., description="ISO country code, or '*' for all"),
    include_deleted: bool = Query(False),
    q: Optional[str] = Query(None, description="Search by business name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List suppliers scoped to a country code. Use '*' for global view."""
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
    items = query.offset((page - 1) * page_size).limit(page_size).all()

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


@router.get("/{code}/suppliers/pending-kyc")
def list_pending_kyc_suppliers(
    code: str = Path(..., description="ISO country code"),
    page: int = 1,
    size: int = 50,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Return suppliers awaiting KYC review for a country."""
    enforce_country_access(code, db=db)
    q = db.query(SupplierProfile).filter(
        SupplierProfile.verification_status.in_(["pending", "documents_submitted", "under_review"]),
        SupplierProfile.is_deleted == False,
    )
    if code != "*":
        q = q.filter(SupplierProfile.country_code == code.upper())
    from utils.pagination import paginated_response
    return paginated_response(
        q.order_by(SupplierProfile.updated_at.desc()),
        page=page,
        size=size,
        serializer=_supplier_to_dict,
    )


@router.get("/{code}/suppliers/{supplier_id}")
def get_supplier_by_country(
    code: str = Path(...),
    supplier_id: int = Path(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    if code != "*" and s.country_code and s.country_code.upper() != code.upper():
        raise HTTPException(403, detail="Supplier does not belong to this country")
    return _supplier_to_dict(s)


@router.put("/{code}/suppliers/{supplier_id}")
def update_supplier_by_country(
    code: str = Path(...),
    supplier_id: int = Path(...),
    business_name: Optional[str] = None,
    verification_status: Optional[str] = None,
    badge_level: Optional[str] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    if code != "*" and s.country_code and s.country_code.upper() != code.upper():
        raise HTTPException(403, detail="Supplier does not belong to this country")
    if business_name is not None:
        s.business_name = business_name
    if verification_status is not None:
        s.verification_status = verification_status
    if badge_level is not None and hasattr(s, "badge_level"):
        s.badge_level = badge_level
    commit_and_refresh(db, s)
    return _supplier_to_dict(s)


@router.post("/{code}/suppliers/{supplier_id}/approve-kyc")
def approve_supplier_kyc(
    code: str = Path(...),
    supplier_id: int = Path(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    s.verification_status = "approved"
    from utils.datetime_utils import utcnow
    s.verified_at = utcnow()
    s.verified_by = admin.id if hasattr(s, "verified_by") else None
    commit_only(db)
    return {"message": "Supplier KYC approved"}


@router.post("/{code}/suppliers/{supplier_id}/reject-kyc")
def reject_supplier_kyc(
    code: str = Path(...),
    supplier_id: int = Path(...),
    reason: Optional[str] = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    s.verification_status = "rejected"
    if hasattr(s, "verification_note"):
        s.verification_note = reason
    commit_only(db)
    return {"message": "Supplier KYC rejected", "reason": reason}


@router.post("/{code}/suppliers/{supplier_id}/suspend")
def suspend_supplier(
    code: str = Path(...),
    supplier_id: int = Path(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    from data.models import User as UserModel
    user = db.query(UserModel).filter(UserModel.id == s.user_id).first()
    if user:
        user.is_active = 0
    commit_only(db)
    return {"message": "Supplier suspended"}


@router.post("/{code}/suppliers/{supplier_id}/activate")
def activate_supplier(
    code: str = Path(...),
    supplier_id: int = Path(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(404, detail="Supplier not found")
    from data.models import User as UserModel
    user = db.query(UserModel).filter(UserModel.id == s.user_id).first()
    if user:
        user.is_active = 1
    commit_only(db)
    return {"message": "Supplier activated"}


@router.post("/{code}/suppliers/{supplier_id}/archive")
def archive_supplier(
    code: str = Path(...),
    supplier_id: int = Path(...),
    payload: Optional[ArchiveRequest] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return archive_entity(
        "supplier_profile",
        supplier_id,
        _user_ctx(current_user),
        db,
        payload.reason if payload else None,
    )


@router.post("/{code}/suppliers/{supplier_id}/restore")
def restore_supplier(
    code: str = Path(...),
    supplier_id: int = Path(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return restore_entity("supplier_profile", supplier_id, _user_ctx(current_user), db)


@router.delete("/{code}/suppliers/{supplier_id}")
def delete_supplier_permanent(
    code: str = Path(...),
    supplier_id: int = Path(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return hard_delete_entity("supplier_profile", supplier_id, _user_ctx(current_user), db)


# ── Legacy global endpoints (kept for backwards-compat, returns all countries) ─

@router.get("")
def list_suppliers_global(
    include_deleted: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Global supplier list (no country filter) — legacy."""
    q = db.query(SupplierProfile)
    if not include_deleted:
        q = q.filter(SupplierProfile.is_deleted == False)
    return [_supplier_to_dict(s) for s in q.offset(skip).limit(limit).all()]


@router.get("/all")
def list_all_suppliers(
    include_deleted: bool = False,
    country: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Legacy paginated supplier list with optional country filter."""
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
    items = query.offset((page - 1) * page_size).limit(page_size).all()

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


# ── Frontend-aligned routes (/admin/suppliers/...) ──────────────────────────────
# The admin UI calls these paths; they mirror the country-scoped handlers above.

@router.get("/suppliers/all")
def list_all_suppliers_frontend(
    include_deleted: bool = False,
    country: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Paginated supplier list used by the admin Suppliers page."""
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
    items = query.offset((page - 1) * page_size).limit(page_size).all()

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


@router.post("/suppliers/bulk")
def bulk_supplier_action(
    payload: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Bulk action across multiple suppliers (verify/reject/suspend/activate/delete/badge)."""
    ids = payload.get("supplier_ids") or []
    action = (payload.get("action") or "").lower()
    note = payload.get("note")
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
            from utils.datetime_utils import utcnow
            if hasattr(s, "verified_at"):
                s.verified_at = utcnow()
        elif action == "reject":
            s.verification_status = "rejected"
        elif action == "suspend":
            s.is_active = False
            if s.user_id:
                u = db.query(User).filter(User.id == s.user_id).first()
                if u:
                    u.is_active = 0
        elif action == "activate":
            s.is_active = True
            if s.user_id:
                u = db.query(User).filter(User.id == s.user_id).first()
                if u:
                    u.is_active = 1
        elif action == "delete":
            if hasattr(s, "is_deleted"):
                s.is_deleted = True
            s.is_active = False
        elif action == "badge":
            if badge_level is not None and hasattr(s, "badge_level"):
                s.badge_level = badge_level
        processed += 1
    commit_only(db)
    return {"processed": processed, "action": action}


@router.post("/suppliers/bulk/restore")
def bulk_restore_suppliers(
    payload: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
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
    commit_only(db)
    return {"processed": processed}


@router.post("/suppliers/{supplier_id}/restore")
def restore_supplier_frontend(
    supplier_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if hasattr(s, "is_deleted"):
        s.is_deleted = False
    s.is_active = True
    commit_only(db)
    return {"message": "Supplier restored", "id": supplier_id}


@router.post("/suppliers/{supplier_id}/refresh-badge")
def refresh_supplier_badge(
    supplier_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    s = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if not hasattr(s, "badge_level"):
        raise HTTPException(status_code=400, detail="Supplier does not support badge levels")
    return {"id": s.id, "badge_level": s.badge_level}


@router.get("/suppliers/documents")
def list_supplier_documents_frontend(
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    import controllers.supplier_document_controller as doc_ctrl
    return doc_ctrl.admin_list_documents(
        {"id": 0, "role": "admin"},
        db,
        supplier_id=supplier_id,
        status=status,
        doc_type=None,
        limit=page_size,
        offset=(page - 1) * page_size,
    )


@router.put("/suppliers/documents/{doc_id}/review")
def review_supplier_document_frontend(
    doc_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    import controllers.supplier_document_controller as doc_ctrl
    return doc_ctrl.admin_review_document(doc_id, data, {"id": 0, "role": "admin"}, db)


@router.get("/suppliers/comparison")
def supplier_comparison_frontend(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Lightweight supplier comparison view (revenue / orders / badges)."""
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _supplier_to_dict(s: SupplierProfile) -> dict:
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

