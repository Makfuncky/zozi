"""Admin supplier management controller."""
from __future__ import annotations

from typing import Any, List, Optional, cast
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import User, SupplierProfile as SP, Notification
from utils.auth import require_permission
from utils.audit import audit_log, AuditAction

from services.write_helpers import add_and_flush, commit_only, flush_only

def bulk_supplier_verification(
    supplier_ids: List[int], action: str, note: Optional[str], acting_user: dict, db: Session
) -> dict:
    """Bulk verify or reject multiple suppliers in one call (admin / sub_admin)."""
    require_permission("moderation.suppliers", acting_user)
    if action not in ("verify", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'verify' or 'reject'")
    if not supplier_ids:
        raise HTTPException(status_code=400, detail="No supplier IDs provided")
    if len(supplier_ids) > 100:
        raise HTTPException(status_code=400, detail="Cannot process more than 100 suppliers at once")

    from models import SupplierProfile as SP

    processed: List[dict] = []
    skipped: List[dict] = []

    for sid in supplier_ids:
        user = db.query(User).filter(User.id == sid, User.role == "supplier").first()
        if not user:
            skipped.append({"id": sid, "reason": "Supplier not found"})
            continue

        profile = db.query(SP).filter(SP.user_id == sid).first()
        if profile is None:
            profile = SP(user_id=sid)
            add_and_flush(db, profile)
            flush_only(db)

        if action == "verify":
            if bool(cast(Any, getattr(user, "is_verified"))) and cast(str | None, getattr(profile, "verification_status")) == "approved":
                skipped.append({"id": sid, "reason": "Already verified"})
                continue
            setattr(user, "is_verified", True)
            setattr(user, "verification_note", note or "Approved")
            setattr(profile, "verification_status", "approved")
            setattr(profile, "verified_at", datetime.now(timezone.utc).replace(tzinfo=None))
            add_and_flush(db, 
   Notification(
                    user_id=user.id,
                    type="account",
                    title="Account Verified",
                    message="Congratulations! Your supplier account has been verified. You can now list products.",
                    link="/supplier/dashboard",
                )
            )
        else:
            setattr(user, "is_verified", False)
            setattr(user, "verification_note", note or "Rejected")
            setattr(profile, "verification_status", "rejected")
            setattr(profile, "verified_at", None)
            add_and_flush(db, 
   Notification(
                    user_id=user.id,
                    type="account",
                    title="Verification Declined",
                    message=f"Your supplier account verification was declined. Reason: {note or 'Please contact support.'}",
                    link="/supplier/dashboard",
                )
            )
        processed.append({"id": sid, "username": user.username})

    if processed:
        commit_only(db)
        audit_log(
            db=db,
            action=AuditAction.SUPPLIER_VERIFIED if action == "verify" else AuditAction.SUPPLIER_REJECTED,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="user",
            resource_id=0,
            details={"bulk": True, "action": action, "count": len(processed), "note": note, "suppliers": processed},
            status="success",
        )
    return {
        "action": action,
        "processed": len(processed),
        "skipped": len(skipped),
        "details": processed,
        "skipped_details": skipped,
    }


def bulk_manage_suppliers(
    supplier_ids: List[int], action: str, note: Optional[str], acting_user: dict, db: Session, badge_level: Optional[str] = None
) -> dict:
    """Bulk supplier lifecycle actions: verify, reject, activate/reactivate, suspend, archive, badge."""
    require_permission("moderation.suppliers", acting_user)
    if not supplier_ids:
        raise HTTPException(status_code=400, detail="No supplier IDs provided")

    normalized_action = str(action or "").strip().lower()
    if normalized_action == "reactivate":
        normalized_action = "activate"
    if normalized_action not in {"verify", "reject", "activate", "suspend", "delete", "badge"}:
        raise HTTPException(
            status_code=400,
            detail="action must be one of: verify, reject, activate, reactivate, suspend, delete, badge",
        )
    if normalized_action in {"delete", "badge"} and acting_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail=f"Only admins can bulk-{normalized_action} suppliers")

    normalized_badge = str(badge_level or "").strip().lower() or None
    valid_badges = {"none", "bronze", "silver", "gold", "membership", "verified"}
    if normalized_action == "badge" and normalized_badge not in valid_badges:
        raise HTTPException(status_code=422, detail=f"badge_level must be one of: {', '.join(sorted(valid_badges))}")

    processed: List[dict] = []
    skipped: List[dict] = []
    note_text = note.strip() if isinstance(note, str) and note.strip() else None

    for supplier_id in list(dict.fromkeys(supplier_ids)):
        user = db.query(User).filter(User.id == supplier_id, User.role == "supplier").first()
        if not user:
            skipped.append({"id": supplier_id, "reason": "Supplier not found"})
            continue

        profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_id).first()
        if profile is None:
            profile = SupplierProfile(user_id=supplier_id)
            add_and_flush(db, profile)
            flush_only(db)

        if normalized_action == "verify":
            setattr(user, "is_verified", True)
            setattr(user, "is_active", True)
            setattr(user, "verification_note", note_text or "Approved")
            setattr(profile, "verification_status", "approved")
            setattr(profile, "verified_at", datetime.now(timezone.utc).replace(tzinfo=None))
        elif normalized_action == "reject":
            setattr(user, "is_verified", False)
            setattr(user, "verification_note", note_text or "Rejected")
            setattr(profile, "verification_status", "rejected")
            setattr(profile, "verified_at", None)
        elif normalized_action == "activate":
            setattr(user, "is_active", True)
            if cast(str | None, getattr(profile, "verification_status", None)) == "archived":
                setattr(profile, "verification_status", "approved" if bool(cast(Any, getattr(user, "is_verified", False))) else "pending")
            if note_text:
                setattr(user, "verification_note", note_text)
        elif normalized_action == "suspend":
            setattr(user, "is_active", False)
            setattr(user, "verification_note", note_text or "Suspended by admin")
        elif normalized_action == "delete":
            setattr(user, "is_active", False)
            setattr(user, "verification_note", note_text or "Archived by admin")
            setattr(profile, "verification_status", "archived")
        elif normalized_action == "badge":
            setattr(profile, "badge_level", normalized_badge)
            setattr(profile, "badge_granted_at", datetime.now(timezone.utc).replace(tzinfo=None))

        processed.append(
            {
                "id": supplier_id,
                "username": user.username,
                "is_active": bool(cast(Any, getattr(user, "is_active", False))),
                "is_verified": bool(cast(Any, getattr(user, "is_verified", False))),
                "verification_status": cast(str | None, getattr(profile, "verification_status", None)),
                "badge_level": cast(str | None, getattr(profile, "badge_level", None)),
                "archived": normalized_action == "delete",
            }
        )

    if processed:
        commit_only(db)
        audit_action = (
            AuditAction.SUPPLIER_VERIFIED
            if normalized_action == "verify"
            else AuditAction.SUPPLIER_REJECTED
            if normalized_action == "reject"
            else "SUPPLIER_BADGE_ASSIGNED"
            if normalized_action == "badge"
            else f"SUPPLIER_{normalized_action.upper()}"
        )
        for supplier_entry in processed:
            audit_log(
                db=db,
                action=audit_action,
                user_id=acting_user["id"],
                username=acting_user.get("username"),
                user_role=acting_user.get("role"),
                resource_type="user",
                resource_id=supplier_entry["id"],
                details={
                    "bulk": True,
                    "action": normalized_action,
                    "note": note_text,
                    "badge_level": normalized_badge,
                    "supplier": supplier_entry,
                },
                status="success",
            )

    return {
        "action": normalized_action,
        "processed": len(processed),
        "skipped": len(skipped),
        "details": processed,
        "skipped_details": skipped,
    }


def get_supplier_comparison(db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    supplier_query = db.query(User).filter(User.role == "supplier")
    total = supplier_query.count()
    suppliers = (
        supplier_query
        .order_by(User.created_at.desc(), User.id.desc())
        .offset(max(0, offset))
        .limit(resolved_limit)
        .all()
    )
    if not suppliers:
        return _build_list_page_payload([], total, offset=offset, page_size=resolved_limit)

    supplier_ids = [s.id for s in suppliers]
    comparison_since = datetime.now(timezone.utc).replace(tzinfo=None)
    recent_since = comparison_since - timedelta(days=30)
    previous_since = comparison_since - timedelta(days=60)

    # Batch: product counts per supplier
    product_count_rows = (
        db.query(Product.supplier_id, func.count(Product.id).label("product_count"))
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .group_by(Product.supplier_id)
        .all()
    )
    product_counts = {
        cast(int, row.supplier_id): int(row.product_count or 0)
        for row in product_count_rows
    }

    # Batch: avg price per supplier
    avg_price_rows = (
        db.query(Product.supplier_id, func.avg(Product.price).label("avg_price"))
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .group_by(Product.supplier_id)
        .all()
    )
    avg_prices = {
        cast(int, row.supplier_id): round(float(row.avg_price or 0), 2)
        for row in avg_price_rows
    }

    # Batch: revenue and order counts per supplier via OrderItem join
    revenue_data: dict[int, float] = {}
    order_count_data: dict[int, int] = {}
    rev_rows = (
        db.query(
            Product.supplier_id,
            func.sum(OrderItem.price * OrderItem.quantity).label("revenue"),
            func.count(func.distinct(OrderItem.order_id)).label("order_count"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .group_by(Product.supplier_id)
        .all()
    )
    for row in rev_rows:
        supplier_id = cast(int, row.supplier_id)
        revenue_data[supplier_id] = float(row.revenue or 0)
        order_count_data[supplier_id] = int(row.order_count or 0)

    recent_rows = (
        db.query(
            Product.supplier_id,
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Product.supplier_id.in_(supplier_ids),
            Product.is_deleted.is_(False),
            Order.created_at >= recent_since,
        )
        .group_by(Product.supplier_id)
        .all()
    )
    previous_rows = (
        db.query(
            Product.supplier_id,
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Product.supplier_id.in_(supplier_ids),
            Product.is_deleted.is_(False),
            Order.created_at >= previous_since,
            Order.created_at < recent_since,
        )
        .group_by(Product.supplier_id)
        .all()
    )
    recent_revenue = {cast(int, row.supplier_id): float(row.revenue or 0) for row in recent_rows}
    previous_revenue = {cast(int, row.supplier_id): float(row.revenue or 0) for row in previous_rows}
    total_revenue = sum(revenue_data.values()) or 0.0

    results = []
    for supplier in suppliers:
        sid = cast(int, supplier.id)
        joined_at = cast(datetime | None, getattr(supplier, "created_at"))
        supplier_revenue = round(revenue_data.get(sid, 0.0), 2)
        current_window = recent_revenue.get(sid, 0.0)
        previous_window = previous_revenue.get(sid, 0.0)
        if previous_window <= 0:
            growth_rate = 100.0 if current_window > 0 else 0.0
        else:
            growth_rate = round(((current_window - previous_window) / previous_window) * 100, 2)
        results.append({
            "id": sid,
            "username": supplier.username,
            "email": supplier.email,
            "product_count": product_counts.get(sid, 0),
            "order_count": order_count_data.get(sid, 0),
            "revenue": supplier_revenue,
            "avg_price": avg_prices.get(sid, 0.0),
            "growth_rate": growth_rate,
            "revenue_share": round((supplier_revenue / total_revenue) * 100, 2) if total_revenue else 0.0,
            "joined": joined_at.isoformat() if joined_at else None,
        })

    results.sort(key=lambda item: item["revenue"], reverse=True)
    return _build_list_page_payload(results, total, offset=offset, page_size=resolved_limit)


def get_pending_suppliers(db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    """Return suppliers who have not yet been verified."""
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    supplier_query = db.query(User).filter(User.role == "supplier", User.is_verified.is_(False))
    total = supplier_query.count()
    suppliers = (
        supplier_query
        .order_by(User.created_at.asc(), User.id.asc())
        .offset(max(0, offset))
        .limit(resolved_limit)
        .all()
    )
    return _build_list_page_payload([
        {
            "id": s.id,
            "username": s.username,
            "email": s.email,
            "phone": s.phone,
            "created_at": s.created_at,
            "is_active": s.is_active,
            "verification_note": getattr(s, "verification_note", None),
        }
        for s in suppliers
    ], total, offset=offset, page_size=resolved_limit)


def verify_supplier(user_id: int, note: Optional[str], acting_user: dict, db: Session) -> dict:
    from models import SupplierProfile, CountryConfig

    user = db.query(User).filter(User.id == user_id, User.role == "supplier").first()
    if not user:
        raise HTTPException(status_code=404, detail="Supplier not found")

    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if profile is None:
        profile = SupplierProfile(user_id=user_id)
        add_and_flush(db, profile)
        flush_only(db)

    if bool(cast(Any, getattr(user, "is_verified"))) and cast(str | None, getattr(profile, "verification_status", None)) == "approved":
        return {"message": "Supplier already verified"}

    # ── Country-specific KYC enforcement ───────────────────────────────────
    supplier_country = str(getattr(user, "preferred_country", "") or "").strip()
    if supplier_country:
        country_config = db.query(CountryConfig).filter(
            CountryConfig.code == supplier_country.upper(),
            CountryConfig.is_active == True,
        ).first()
        if country_config:
            req_raw = country_config.supplier_requirements_json
            if req_raw:
                try:
                    import json
                    requirements = json.loads(req_raw) if isinstance(req_raw, str) else req_raw
                except (json.JSONDecodeError, TypeError):
                    requirements = {}
                if isinstance(requirements, dict):
                    required_docs = requirements.get("required_documents", [])
                    if required_docs and isinstance(required_docs, list):
                        from models import SupplierDocument
                        approved_types = set()
                        for doc in db.query(SupplierDocument).filter(
                            SupplierDocument.supplier_id == user_id,
                            SupplierDocument.status == "approved",
                        ).all():
                            approved_types.add(str(getattr(doc, "document_type", "")).strip().lower())

                        missing = [
                            d for d in required_docs
                            if str(d).strip().lower() not in approved_types
                        ]
                        if missing:
                            raise HTTPException(
                                status_code=422,
                                detail=f"Supplier missing required documents for country '{supplier_country}': {', '.join(missing)}. Required: {required_docs}",
                            )

    setattr(user, "is_verified", True)
    setattr(user, "verification_note", note or "Approved")
    setattr(profile, "verification_status", "approved")
    setattr(profile, "verified_at", datetime.now(timezone.utc).replace(tzinfo=None))
    add_and_flush(db, 
   Notification(
            user_id=user.id,
            type="account",
            title="Account Verified",
            message="Congratulations! Your supplier account has been verified. You can now list products.",
            link="/supplier/dashboard",
        )
    )
    commit_only(db)
    audit_log(
        db=db,
        action=AuditAction.SUPPLIER_VERIFIED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"supplier_username": user.username, "note": note},
        status="success",
    )
    return {"message": "Supplier verified", "supplier_id": user_id, "username": user.username}


def reject_supplier(user_id: int, note: Optional[str], acting_user: dict, db: Session) -> dict:
    from models import SupplierProfile

    user = db.query(User).filter(User.id == user_id, User.role == "supplier").first()
    if not user:
        raise HTTPException(status_code=404, detail="Supplier not found")

    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if profile is None:
        profile = SupplierProfile(user_id=user_id)
        add_and_flush(db, profile)
        flush_only(db)

    setattr(user, "is_verified", False)
    setattr(user, "verification_note", note or "Rejected")
    setattr(profile, "verification_status", "rejected")
    setattr(profile, "verified_at", None)
    add_and_flush(db, 
   Notification(
            user_id=user.id,
            type="account",
            title="Verification Declined",
            message=f"Your supplier account verification was declined. Reason: {note or 'Please contact support.'}",
            link="/supplier/dashboard",
        )
    )
    commit_only(db)
    audit_log(
        db=db,
        action=AuditAction.SUPPLIER_REJECTED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="user",
        resource_id=user_id,
        details={"supplier_username": user.username, "note": note},
        status="success",
    )
    return {"message": "Supplier verification rejected", "supplier_id": user_id, "username": user.username}


# â”€â”€ Product Moderation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def get_all_suppliers(
    db: Session,
    *,
    skip: int = 0,
    limit: int | None = None,
    q: Optional[str] = None,
    status: Optional[str] = None,
    badge: Optional[str] = None,
) -> dict:
    """Return suppliers with summary profile, activity metrics, and server-side filters."""
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))

    query = (
        db.query(User)
        .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
        .filter(User.role == "supplier")
    )

    normalized_query = (q or "").strip()
    if normalized_query:
        like = f"%{normalized_query}%"
        query = query.filter(
            or_(
                User.username.ilike(like),
                User.email.ilike(like),
                SupplierProfile.business_name.ilike(like),
            )
        )

    normalized_status = (status or "").strip().lower()
    if normalized_status and normalized_status != "all":
        if normalized_status == "pending":
            query = query.filter(User.is_active.in_([True, 1])).filter(
                or_(
                    SupplierProfile.verification_status.is_(None),
                    SupplierProfile.verification_status.in_(["pending", "under_review", "documents_submitted"]),
                )
            )
        elif normalized_status in {"approved", "verified"}:
            query = query.filter(User.is_active.in_([True, 1])).filter(
                or_(
                    SupplierProfile.verification_status.in_(["approved", "verified"]),
                    User.is_verified.is_(True),
                )
            )
        elif normalized_status == "rejected":
            query = query.filter(SupplierProfile.verification_status == "rejected")
        elif normalized_status in {"suspended", "archived"}:
            query = query.filter(User.is_active.in_([False, 0]))
        elif normalized_status == "active":
            query = query.filter(User.is_active.in_([True, 1]))

    normalized_badge = (badge or "").strip().lower()
    if normalized_badge and normalized_badge != "all":
        query = query.filter(SupplierProfile.badge_level == normalized_badge)

    total = query.count()
    suppliers = (
        query
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(resolved_limit)
        .all()
    )

    supplier_ids = [cast(int, supplier.id) for supplier in suppliers]
    profiles = {
        cast(int, profile.user_id): profile
        for profile in db.query(SupplierProfile).filter(SupplierProfile.user_id.in_(supplier_ids)).all()
    } if supplier_ids else {}

    product_metric_rows = (
        db.query(
            Product.supplier_id,
            func.count(Product.id).label("product_count"),
            func.avg(Product.price).label("avg_price"),
        )
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .group_by(Product.supplier_id)
        .all()
    ) if supplier_ids else []
    product_metrics = {
        cast(int, row.supplier_id): {
            "product_count": int(row.product_count or 0),
            "avg_price": round(float(row.avg_price or 0), 2),
        }
        for row in product_metric_rows
    }

    revenue_rows = (
        db.query(
            Product.supplier_id,
            func.count(func.distinct(OrderItem.order_id)).label("order_count"),
            func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .group_by(Product.supplier_id)
        .all()
    ) if supplier_ids else []
    revenue_metrics = {
        cast(int, row.supplier_id): {
            "order_count": int(row.order_count or 0),
            "revenue": round(float(row.revenue or 0), 2),
        }
        for row in revenue_rows
    }

    top_product_rows = (
        db.query(Product.supplier_id, Product.name, Product.sales_count)
        .filter(Product.supplier_id.in_(supplier_ids), Product.is_deleted.is_(False))
        .order_by(Product.supplier_id.asc(), Product.sales_count.desc(), Product.created_at.desc())
        .all()
    ) if supplier_ids else []
    top_products: dict[int, str | None] = {}
    for row in top_product_rows:
        supplier_id = cast(int, row.supplier_id)
        if supplier_id not in top_products:
            top_products[supplier_id] = cast(str | None, row.name)

    summary = {
        "pending_suppliers": int(
            (
                db.query(func.count(User.id))
                .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
                .filter(
                    User.role == "supplier",
                    User.is_active.in_([True, 1]),
                    or_(
                        SupplierProfile.verification_status.is_(None),
                        SupplierProfile.verification_status.in_(["pending", "under_review", "documents_submitted"]),
                    ),
                )
                .scalar()
            ) or 0
        ),
        "active_suppliers": int((db.query(func.count(User.id)).filter(User.role == "supplier", User.is_active.in_([True, 1])).scalar()) or 0),
        "suspended_suppliers": int((db.query(func.count(User.id)).filter(User.role == "supplier", User.is_active.in_([False, 0])).scalar()) or 0),
        "total_revenue": round(
            float(
                (
                    db.query(func.coalesce(func.sum(OrderItem.price * OrderItem.quantity), 0))
                    .join(Product, Product.id == OrderItem.product_id)
                    .join(User, User.id == Product.supplier_id)
                    .filter(User.role == "supplier", Product.is_deleted.is_(False))
                    .scalar()
                ) or 0
            ),
            2,
        ),
    }

    items = []
    for supplier in suppliers:
        profile = profiles.get(cast(int, supplier.id))
        metrics = product_metrics.get(cast(int, supplier.id), {})
        revenue = revenue_metrics.get(cast(int, supplier.id), {})
        verified_at = cast(datetime | None, getattr(profile, "verified_at", None)) if profile else None
        items.append(
            {
                "id": supplier.id,
                "username": supplier.username,
                "email": supplier.email,
                "phone": supplier.phone,
                "is_active": supplier.is_active,
                "is_verified": supplier.is_verified,
                "verification_note": getattr(profile, "verification_note", None) if profile else None,
                "created_at": supplier.created_at,
                "product_count": int(metrics.get("product_count", 0)),
                "order_count": int(revenue.get("order_count", 0)),
                "revenue": float(revenue.get("revenue", 0)),
                "avg_price": float(metrics.get("avg_price", 0)),
                "top_product_name": top_products.get(cast(int, supplier.id)),
                "profile": {
                    "business_name": profile.business_name if profile else None,
                    "business_type": profile.business_type if profile else None,
                    "country": profile.country_code if profile else None,
                    "region": profile.region if profile else None,
                    "city": profile.city if profile else None,
                    "website": profile.website if profile else None,
                    "phone_business": profile.phone_business if profile else None,
                    "tax_id": profile.tax_id if profile else None,
                    "verification_status": profile.verification_status if profile else "pending",
                    "badge_level": profile.badge_level if profile else None,
                    "credibility_score": profile.credibility_score if profile else 0,
                    "verified_at": verified_at.isoformat() if verified_at else None,
                } if profile else None,
            }
        )

    page = (skip // resolved_limit) + 1 if resolved_limit else 1
    total_pages = max(1, ((total - 1) // resolved_limit) + 1) if resolved_limit else 1

    return {
        "items": items,
        "summary": summary,
        "total": total,
        "page": page,
        "page_size": resolved_limit,
        "total_pages": total_pages,
        "skip": skip,
        "limit": resolved_limit,
        "filters": {
            "q": normalized_query or None,
            "status": normalized_status or "all",
            "badge": normalized_badge or "all",
        },
    }


