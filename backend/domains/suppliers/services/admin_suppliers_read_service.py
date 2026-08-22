"""Read helpers for admin supplier routers (Law 2: routers stay thin).

These functions own the SupplierProfile ORM queries that previously lived inline
in `modules/admin/routers/admin_suppliers.py`. Behavior (query shape, filters,
ordering, returned dict keys/values, status codes) is preserved exactly.
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.suppliers.models import SupplierProfile
from domains.country.utils.country_rls import enforce_country_access
from infrastructure.utils.pagination import paginated_response
from infrastructure.utils.pagination import keyset_offset_window




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
