"""Auto-migrated service logic from routers/admin_products.py."""

from __future__ import annotations



from fastapi import Body, Depends, HTTPException, Path, Query



from sqlalchemy.orm import Session



from domains.governance.services.settings.misc_service import (
    archive_entity,
    restore_entity,
    hard_delete_entity,
)
from domains.catalog.services.products.bulk_ops_write_service import (
    bulk_archive_entities,
    bulk_restore_entities,
)
from domains.governance.services.products.admin_catalog_operations_service import (
    bulk_category_change,
    bulk_product_moderation,
)



from domains.catalog.services.products.products_service import _bump_product_cache_version



from infrastructure.database.database import get_db



from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest, BulkCategoryChangeRequest



from domains.catalog.models.products import Product



from domains.country.utils.country_rls import get_country_or_404



from infrastructure.utils.dependencies import require_admin, require_super_admin



from infrastructure.utils.pagination import paginated_response



from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context



def list_all_products(country_code: str, page: int, size: int, moderation_status: str, include_deleted: bool, _, db: Session):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        q = db.query(Product).filter(Product.country_code == country_code.upper())

        if moderation_status: q = q.filter(Product.moderation_status == moderation_status)

        if not include_deleted: q = q.filter(Product.is_deleted == False)

        return paginated_response(q, page, size)

    finally:

        clear_rls_context()



def approve_product(country_code: str, product_id: int, _, db: Session):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()

        if not p: raise HTTPException(404)

        p.moderation_status = "approved"; p.is_verified = True

        db.commit()

        _bump_product_cache_version()

        return {"message": "Product approved"}

    finally:

        clear_rls_context()



def reject_product(country_code: str, product_id: int, reason: str, _, db: Session):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()

        if not p: raise HTTPException(404)

        p.moderation_status = "rejected"; p.moderation_notes = reason

        db.commit()

        _bump_product_cache_version()

        return {"message": "Product rejected"}

    finally:

        clear_rls_context()



def update_product_badge(country_code: str, product_id: int, field: str, value: bool, _, db: Session):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        p = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()

        if not p: raise HTTPException(404)

        if field not in ("is_hot", "is_featured"):

            raise HTTPException(400, "field must be 'is_hot' or 'is_featured'")

        setattr(p, field, value)

        db.commit()

        _bump_product_cache_version()

        return {"message": "Product badge updated", "field": field, "value": value}

    finally:

        clear_rls_context()



def bulk_archive_products(country_code: str, payload: BulkActionRequest, _, db: Session, current_user):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        return bulk_archive_entities("product", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)

    finally:

        clear_rls_context()



def bulk_restore_products(country_code: str, payload: BulkActionRequest, _, db: Session, current_user):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        return bulk_restore_entities("product", payload.ids, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)

    finally:

        clear_rls_context()



def bulk_moderate_products(country_code: str, payload: dict, _, db: Session, current_user):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        product_ids = payload.get("product_ids", [])

        action = payload.get("action")

        if not product_ids or action not in ("approve", "reject"):

            raise HTTPException(400, "product_ids and action (approve/reject) are required")

        return bulk_product_moderation(product_ids, action, payload.get("note"), {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)

    finally:

        clear_rls_context()



def bulk_change_category(country_code: str, payload: BulkCategoryChangeRequest, _, db: Session, current_user):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        return bulk_category_change(payload.ids, payload.category_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason)

    finally:

        clear_rls_context()



def archive_product(country_code: str, product_id: int, payload: ArchiveRequest, _, db: Session, current_user):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        return archive_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db, payload.reason if payload else None)

    finally:

        clear_rls_context()



def restore_product_route(country_code: str, product_id: int, _, db: Session, current_user):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        return restore_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)

    finally:

        clear_rls_context()



def delete_product_permanent(country_code: str, product_id: int, _, db: Session, current_user):

    get_country_or_404(country_code.upper(), db)

    set_rls_context({country_code.upper()}, is_restricted=True)

    try:

        return hard_delete_entity("product", product_id, {"id": current_user.id, "username": current_user.username, "role": current_user.role}, db)

    finally:

        clear_rls_context()

# -- Route wrapper functions (called via products_controller) -------------------

def approve_product_route(country_code: str, product_id: int, current_user: dict, db: Session) -> dict:
    return approve_product(country_code, product_id, current_user, db)

def reject_product_route(country_code: str, product_id: int, current_user: dict, db: Session) -> dict:
    return reject_product(country_code, product_id, "", current_user, db)

def toggle_product_badge_route(country_code: str, product_id: int, current_user: dict, db: Session, field: str = "is_hot", value: bool = True) -> dict:
    return update_product_badge(country_code, product_id, field, value, current_user, db)

def bulk_delete_products_route(country_code: str, current_user: dict, db: Session, ids: list[int], reason: str | None = None) -> dict:
    from infrastructure.database.schemas import BulkActionRequest
    payload = BulkActionRequest(ids=ids, reason=reason)
    return bulk_archive_products(country_code, payload, current_user, db, current_user)

def unarchive_product_route(country_code: str, product_id: int, current_user: dict, db: Session) -> dict:
    return restore_product_route(country_code, product_id, current_user, db)

def list_pending_products(country_code: str, page: int = 1, page_size: int = 20, current_user: dict | None = None, db: Session | None = None) -> dict:
    return list_all_products(country_code, page, page_size, "pending", False, current_user, db)


def _normalize_image_path(path: str | None) -> str:
    if not path:
        return ""
    return path


def _build_list_page_payload(items: list, total: int, offset: int = 0, page_size: int | None = None) -> dict:
    resolved_page_size = page_size if page_size is not None else len(items)
    if resolved_page_size <= 0:
        resolved_page_size = max(total, 1)
    return {
        "data": items,
        "total": total,
        "offset": offset,
        "page_size": resolved_page_size,
        "pages": (total + resolved_page_size - 1) // resolved_page_size if total > 0 else 0,
    }


def _variant_to_dict(variant: Any) -> dict[str, Any]:
    cols = [c.name for c in variant.__table__.columns] if hasattr(variant, "__table__") else []
    d = {}
    for col in cols:
        val = getattr(variant, col, None)
        if isinstance(val, Decimal):
            val = float(val)
        d[col] = val
    return d


def _product_to_dict(product: Product) -> dict[str, Any]:
    cols = [c.name for c in Product.__table__.columns]
    d = {}
    for col in cols:
        val = getattr(product, col, None)
        if isinstance(val, Decimal):
            val = float(val)
        d[col] = val
    if hasattr(product, "variants") and product.variants:
        d["variants"] = [_variant_to_dict(v) for v in product.variants]
    return d


def bulk_delete_products_admin(product_ids: List[int], acting_user: dict, db: Session) -> dict:
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
        db.commit()
    return {"deleted": len(deleted), "skipped": len(skipped), "details": deleted, "skipped_details": skipped}


def bulk_product_moderation(product_ids: List[int], action: str, note: Optional[str], acting_user: dict, db: Session) -> dict:
    if not product_ids:
        raise HTTPException(status_code=400, detail="No product IDs provided")
    products = db.query(Product).filter(Product.id.in_(product_ids), Product.is_deleted.is_(False)).all()
    found_ids = {cast(int, p.id) for p in products}
    processed: List[dict] = []
    skipped: List[dict] = []
    for product in products:
        if action == "approve":
            setattr(product, "is_approved", True)
            setattr(product, "is_active", True)
        else:
            setattr(product, "is_approved", False)
            setattr(product, "is_active", False)
        processed.append({"id": product.id, "name": product.name})
    for pid in product_ids:
        if pid not in found_ids:
            skipped.append({"id": pid, "reason": "Not found or deleted"})
    if processed:
        db.commit()
    return {"action": action, "processed": len(processed), "skipped": len(skipped), "details": processed, "skipped_details": skipped}


def get_all_products(db: Session, limit: Optional[int] = None, offset: int = 0, search: Optional[str] = None, filter_value: Optional[str] = None) -> dict[str, Any]:
    from infrastructure.utils.constants import _ADMIN_DEFAULT_PAGE_SIZE, _ADMIN_MAX_PAGE_SIZE
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
    items = [_product_to_dict(p) for p in products]
    return _build_list_page_payload(items, total, offset=offset, page_size=resolved_limit)


def delete_product_admin(product_id: int, acting_user: dict, db: Session) -> dict:
    from domains.governance.models.core import CartItem
    from domains.catalog.models.products import Wishlist, Review
    from domains.comms.models.communication import Notification as NotifModel
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product_name = str(product.name)
    db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)
    db.query(Wishlist).filter(Wishlist.product_id == product_id).delete(synchronize_session=False)
    db.query(Review).filter(Review.product_id == product_id, Review.is_deleted == False).update({"is_deleted": True}, synchronize_session=False)
    setattr(product, "is_deleted", True)
    db.commit()
    return {"message": "Product deleted"}


def restore_product_admin(product_id: int, acting_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not bool(cast(Any, getattr(product, "is_deleted"))):
        raise HTTPException(status_code=400, detail="Product is not archived")
    setattr(product, "is_deleted", False)
    db.commit()
    return {"message": "Product restored"}


def toggle_product_badge(product_id: int, field: str, value: bool, acting_user: dict, db: Session) -> dict:
    allowed = {"is_hot", "is_featured", "is_new"}
    if field not in allowed:
        raise HTTPException(status_code=400, detail=f"field must be one of {allowed}")
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    setattr(product, field, value)
    db.commit()
    return {"message": f"{field} set to {value}", "product_id": product_id}
