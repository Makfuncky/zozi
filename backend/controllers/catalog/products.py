"""Admin product management controller."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, cast
from decimal import Decimal
import uuid

from fastapi import HTTPException
from sqlalchemy import or_, func, String, cast as sql_cast
from sqlalchemy.orm import Session, selectinload

from models import (
    Product, Order, OrderItem, CartItem, Wishlist, Review,
    Notification, User, AuditLog
)
from services.catalog.product_utils import _bump_product_cache_version
from utils.auth import require_permission
from utils.audit import audit_log, AuditAction
from utils.constants import _ADMIN_DEFAULT_PAGE_SIZE, _ADMIN_MAX_PAGE_SIZE

from services.write_helpers import add_and_flush, commit_only
# Module-level helper functions


def _normalize_image_path(path: str | None) -> str:
    """Normalize image path for storage."""
    if not path:
        return ""
    return path


def _build_list_page_payload(items: list, total: int, offset: int, page_size: int) -> dict:
    """Build a paginated list response payload."""
    return {
        "data": items,
        "total": total,
        "offset": offset,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


def bulk_delete_products_admin(product_ids: List[int], acting_user: dict, db: Session) -> dict:
    """Bulk soft-delete multiple products (admin / moderator)."""
    require_permission("products.manage", acting_user)
    if not product_ids:
        raise HTTPException(status_code=400, detail="No product IDs provided")
    if len(product_ids) > 200:
        raise HTTPException(status_code=400, detail="Cannot delete more than 200 products at once")

    products = db.query(Product).options(selectinload(Product.variants), selectinload(Product.reviews)).filter(Product.id.in_(product_ids)).all()
    found_ids = {cast(int, p.id) for p in products}
    deleted: List[dict] = []
    skipped: List[dict] = []

    for product in products:
        if bool(cast(Any, getattr(product, "is_deleted"))):
            skipped.append({"id": product.id, "reason": "Already deleted"})
            continue
        setattr(product, "is_deleted", True)
        deleted.append({"id": product.id, "name": product.name})

    for pid in product_ids:
        if pid not in found_ids:
            skipped.append({"id": pid, "reason": "Not found"})

    if deleted:
        commit_only(db)
        audit_log(
            db=db,
            action=AuditAction.PRODUCT_DELETE,
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="product",
            resource_id=0,
            details={"bulk": True, "deleted_count": len(deleted), "products": deleted},
            status="success",
        )
    return {
        "deleted": len(deleted),
        "skipped": len(skipped),
        "details": deleted,
        "skipped_details": skipped,
    }


def bulk_product_moderation(
    product_ids: List[int], action: str, note: Optional[str], acting_user: dict, db: Session
) -> dict:
    """Bulk approve or reject multiple products in one call (admin / moderator)."""
    require_permission("moderation.products", acting_user)
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")
    if not product_ids:
        raise HTTPException(status_code=400, detail="No product IDs provided")
    if len(product_ids) > 200:
        raise HTTPException(status_code=400, detail="Cannot moderate more than 200 products at once")

    products = db.query(Product).filter(
        Product.id.in_(product_ids),
        Product.is_deleted.is_(False),
    ).all()
    found_ids = {cast(int, p.id) for p in products}
    processed: List[dict] = []
    skipped: List[dict] = []

    for product in products:
        if action == "approve":
            setattr(product, "is_approved", True)
            setattr(product, "is_active", True)
            add_and_flush(db, 
   Notification(
                    user_id=product.supplier_id,
                    type="product",
                    title="Product Approved",
                    message=f'Your product "{product.name}" has been approved and is now live.',
                    link=f"/products/{product.id}",
                )
            )
        else:
            setattr(product, "is_approved", False)
            setattr(product, "is_active", False)
            add_and_flush(db, 
   Notification(
                    user_id=product.supplier_id,
                    type="product",
                    title="Product Rejected",
                    message=f'Your product "{product.name}" was not approved. Reason: {note or "Does not meet listing standards."}',
                    link="/supplier/products",
                )
            )
        processed.append({"id": product.id, "name": product.name})

    for pid in product_ids:
        if pid not in found_ids:
            skipped.append({"id": pid, "reason": "Not found or deleted"})

    if processed:
        commit_only(db)
        audit_log(
            db=db,
            action="PRODUCT_APPROVED" if action == "approve" else "PRODUCT_REJECTED",
            user_id=acting_user["id"],
            username=acting_user.get("username"),
            user_role=acting_user.get("role"),
            resource_type="product",
            resource_id=0,
            details={"bulk": True, "action": action, "count": len(processed), "note": note, "products": processed},
            status="success",
        )
    return {
        "action": action,
        "processed": len(processed),
        "skipped": len(skipped),
        "details": processed,
        "skipped_details": skipped,
    }


# â”€â”€ Bulk Supplier Verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _product_to_dict(product: Product) -> dict[str, Any]:
    cols = [c.name for c in Product.__table__.columns]
    d = {}
    for col in cols:
        val = getattr(product, col, None)
        if isinstance(val, Decimal):
            val = float(val)
        d[col] = val
    # Handle relationships
    if hasattr(product, "variants") and product.variants:
        d["variants"] = [_variant_to_dict(v) for v in product.variants]
    return d


def _variant_to_dict(variant: Any) -> dict[str, Any]:
    cols = [c.name for c in variant.__table__.columns] if hasattr(variant, "__table__") else []
    d = {}
    for col in cols:
        val = getattr(variant, col, None)
        if isinstance(val, Decimal):
            val = float(val)
        d[col] = val
    return d


def get_all_products(
    db: Session,
    limit: Optional[int] = None,
    offset: int = 0,
    search: Optional[str] = None,
    filter_value: Optional[str] = None,
) -> dict[str, Any]:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    query = db.query(Product).options(selectinload(Product.variants))
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(term),
                Product.category.ilike(term),
                Product.brand.ilike(term),
                func.cast(Product.id, String).ilike(term),
            )
        )
    if filter_value == "deleted":
        query = query.filter(Product.is_deleted.is_(True))
    else:
        query = query.filter(Product.is_deleted.is_(False))
        if filter_value == "pending":
            query = query.filter(Product.is_approved.is_(False))
        elif filter_value == "approved":
            query = query.filter(Product.is_approved.is_(True))
        elif filter_value == "rejected":
            query = query.filter(Product.is_approved.is_(False))
    query = query.order_by(Product.created_at.desc(), Product.id.desc())
    total = query.count()
    if offset:
        query = query.offset(offset)
    query = query.limit(resolved_limit)
    products = query.all()
    # Serialize ORM objects to dicts for Pydantic response model
    items = [_product_to_dict(p) for p in products]
    return _build_list_page_payload(items, total, offset=offset, page_size=resolved_limit)


def delete_product_admin(product_id: int, acting_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_name = str(product.name)

    # --- Cascade 1: Remove from all carts ---
    db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)

    # --- Cascade 2: Remove from all wishlists ---
    db.query(Wishlist).filter(Wishlist.product_id == product_id).delete(synchronize_session=False)

    # --- Cascade 3: Soft-delete reviews (preserve data history) ---
    db.query(Review).filter(
        Review.product_id == product_id,
        Review.is_deleted == False,  # noqa: E712
    ).update({"is_deleted": True}, synchronize_session=False)

    # --- Cascade 4: Notify users with pending/processing orders that include this product ---
    affected_orders = (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(
            OrderItem.product_id == product_id,
            Order.status.in_(["pending", "processing", "confirmed"]),
        )
        .all()
    )
    for order in affected_orders:
        add_and_flush(db, Notification(
            user_id=order.user_id,
            type="system",
            title="Product Unavailable",
            message=(
                f"A product ('{product_name}') in your order #{order.id} "
                "is no longer available. Our support team will contact you."
            ),
            link=f"/orders/{order.id}",
        ))

    # --- Soft-delete the product itself ---
    setattr(product, "is_deleted", True)
    commit_only(db)
    _bump_product_cache_version()

    audit_log(
        db=db,
        action=AuditAction.PRODUCT_DELETE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={
            "product_name": product_name,
            "carts_cleared": True,
            "wishlists_cleared": True,
            "reviews_archived": True,
            "orders_notified": len(affected_orders),
        },
        status="success",
    )
    return {"message": "Product deleted", "orders_notified": len(affected_orders)}


def restore_product_admin(product_id: int, acting_user: dict, db: Session) -> dict:
    """Restore a soft-deleted product (admin only)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not bool(cast(Any, getattr(product, "is_deleted"))):
        raise HTTPException(status_code=400, detail="Product is not archived")
    setattr(product, "is_deleted", False)
    commit_only(db)
    _bump_product_cache_version()
    audit_log(
        db=db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"product_name": product.name, "action": "restore"},
        status="success",
    )
    return {"message": "Product restored"}


# ── Soft-delete / Archive / Restore entity wrappers ─────────────────────────

def get_pending_products(db: Session, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    """Return products pending admin approval."""
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    product_query = db.query(Product).filter(Product.is_approved.is_(False), Product.is_deleted.is_(False))
    total = product_query.count()
    products = (
        product_query
        .order_by(Product.created_at.asc(), Product.id.asc())
        .offset(max(0, offset))
        .limit(resolved_limit)
        .all()
    )
    return _build_list_page_payload([
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "supplier_id": p.supplier_id,
            "image_url": _normalize_image_path(cast(str | None, getattr(p, "image_url"))),
            "created_at": p.created_at,
        }
        for p in products
    ], total, offset=offset, page_size=resolved_limit)


def toggle_product_badge(
    product_id: int,
    field: str,
    value: bool,
    acting_user: dict,
    db: Session,
) -> dict:
    """Set is_hot, is_featured, or is_new on a product."""
    allowed = {"is_hot", "is_featured", "is_new"}
    if field not in allowed:
        raise HTTPException(status_code=400, detail=f"field must be one of {allowed}")
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    setattr(product, field, value)
    commit_only(db)
    audit_log(
        db=db,
        action=f"PRODUCT_BADGE_{field.upper()}_{'ON' if value else 'OFF'}",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"product_name": product.name, "field": field, "value": value},
        status="success",
    )
    return {"message": f"{field} set to {value}", "product_id": product_id}


def approve_product(product_id: int, acting_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from controllers.country_controller import is_product_restricted_for_country
    supplier = db.query(User).filter(User.id == product.supplier_id).first()
    if supplier:
        supplier_country = str(getattr(supplier, "preferred_country", "") or "").strip()
        if supplier_country:
            product_category = str(getattr(product, "category", "") or "").strip().lower()
            if is_product_restricted_for_country(product_category, supplier_country, db):
                raise HTTPException(
                    status_code=422,
                    detail=f"Product category '{product_category}' is restricted in the supplier's country ({supplier_country}).",
                )

    setattr(product, "is_approved", True)
    setattr(product, "is_active", True)
    add_and_flush(db, 
   Notification(
            user_id=product.supplier_id,
            type="product",
            title="Product Approved",
            message=f'Your product "{product.name}" has been approved and is now live.',
            link=f"/products/{product.id}",
        )
    )
    commit_only(db)
    audit_log(
        db=db,
        action="PRODUCT_APPROVED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"product_name": product.name},
        status="success",
    )
    return {"message": "Product approved", "product_id": product_id}


def reject_product(product_id: int, note: Optional[str], acting_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    setattr(product, "is_approved", False)
    setattr(product, "is_active", False)
    add_and_flush(db, 
   Notification(
            user_id=product.supplier_id,
            type="product",
            title="Product Rejected",
            message=f'Your product "{product.name}" was not approved. Reason: {note or "Does not meet listing standards."}',
            link="/supplier/products",
        )
    )
    commit_only(db)
    audit_log(
        db=db,
        action="PRODUCT_REJECTED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"product_name": product.name, "note": note},
        status="success",
    )
    return {"message": "Product rejected", "product_id": product_id}


# â”€â”€ Coupon Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

