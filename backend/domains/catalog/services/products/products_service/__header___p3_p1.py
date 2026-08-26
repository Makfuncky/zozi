"""
def get_supplier_products_simple(current_user: dict, db: Session) -> List[Product]:
    return db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).all()


def create_supplier_product_with_upload(
    name: str,
    description: str,
    price: float,
    category: str,
    color: str,
    stock: int,
    file: UploadFile,
    current_user: dict,
    db: Session,
) -> Product:
    from infrastructure.utils.file_validation import validate_upload_image
    from infrastructure.utils.storage import storage as _storage

    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    content = file.file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Image file exceeds 10MB limit")

    validated_ext = validate_upload_image(content, file.filename or "upload")
    safe_filename = f"{uuid.uuid4().hex}{validated_ext}"
    key = f"products/{safe_filename}"
    url = _storage.save(key, content, content_type=file.content_type)

    product = Product(
        name=html.escape(name.strip()) if name else name,
        description=html.escape(description) if description else description,
        price=price,
        category=category,
        color=color,
        image_url=url,
        stock=stock,
        supplier_id=current_user["id"],
    )
    category_match = db.query(Category).filter(
        or_(func.lower(Category.name) == category.strip().casefold(), func.lower(Category.slug) == category.strip().casefold())
    ).first() if category and category.strip() else None
    if category_match is not None:
        product.category_id = cast(int, getattr(category_match, "id"))
        product.category = cast(str, getattr(category_match, "name"))
    db.add(product)
    db.commit()
    _bump_product_cache_version()
    db.refresh(product)
    return product


def autocomplete_products(q: str, db: Session) -> List[str]:
    term = f"%{q.lower()}%"
    results = db.query(Product.name).filter(Product.name.ilike(term)).limit(10).all()
    return [r[0] for r in results]


def get_supplier_names(db: Session) -> List[str]:
    """Return supplier usernames and storefront business names for filtering."""
    results = (
        db.query(User.username, SupplierProfile.business_name)
        .join(Product, Product.supplier_id == User.id)
        .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
        .filter(
            User.role == "supplier",
            Product.is_deleted == False,  # noqa: E712
            Product.is_active.isnot(False),
            Product.is_approved.isnot(False),
        )
        .order_by(User.username)
        .all()
    )
    names: list[str] = []
    seen: set[str] = set()
    for username, business_name in results:
        for candidate in (business_name, username):
            if not candidate:
                continue
            normalized = candidate.strip()
            key = normalized.lower()
            if not normalized or key in seen:
                continue
            seen.add(key)
            names.append(normalized)
    return names


def get_product_by_barcode(code: str, db: Session) -> Product:
    """
    Barcode / QR lookup compatibility layer.

    Supported payload shapes:
    - "123"          -> product id
    - "P-123"        -> product id
    - "PROD-123"     -> product id
    - "PRODUCT-123"  -> product id
    """
    raw = (code or "").strip()
    if not raw:
        raise HTTPException(status_code=422, detail="Barcode is required")

    upper = raw.upper()
    candidates = [upper]
    for prefix in ("P-", "PROD-", "PRODUCT-"):
        if upper.startswith(prefix):
            candidates.append(upper[len(prefix):])

    product_id = None
    for candidate in candidates:
        if candidate.isdigit():
            product_id = int(candidate)
            break

    product = None
    if product_id is not None:
        product = db.query(Product).options(selectinload(Product.variants)).filter(
            Product.id == product_id,
            Product.is_deleted == False,   # noqa: E712
            Product.is_active == True,     # noqa: E712
            Product.is_approved == True,   # noqa: E712
        ).first()
    if not product:
        matched_variant = (
            db.query(ProductVariant)
            .options(selectinload(ProductVariant.product).selectinload(Product.variants))
            .filter(
                ProductVariant.is_active == True,  # noqa: E712
                or_(
                    ProductVariant.barcode == raw,
                    ProductVariant.product_code == raw,
                    ProductVariant.sku == raw,
                ),
            )
            .first()
        )
        if matched_variant and matched_variant.product:
            product = matched_variant.product
            if product.is_deleted or not product.is_active or not product.is_approved:
                raise HTTPException(status_code=404, detail="Product not found for the scanned barcode")
    if not product:
        raise HTTPException(
            status_code=404,
            detail="No product matched this barcode. Use numeric product code, P-<id>, SKU, barcode, or product code.",
        )
    return product


def get_recommended_products(current_user: Optional[dict], limit: int, db: Session) -> List[Product]:
    """Return personalised products based on browsing history, fall back to top sellers."""
    import json as _json
    from sqlalchemy.orm import selectinload
    categories: list[str] = []

    if current_user:
        user = (
            db.query(User)
            .filter(User.id == current_user["id"])
            .first()
        )
        browsing_history_json = getattr(user, "browsing_history_json", None) if user else None
        if user and browsing_history_json:
            try:
                history: list[int] = _json.loads(browsing_history_json)[-20:]
                if history:
                    viewed = (
                        db.query(Product)
                        .options(selectinload(Product.variants))
                        .filter(Product.id.in_(history))
                        .all()
                    )
                    categories = list({cast(str, getattr(p, "category")) for p in viewed if cast(str | None, getattr(p, "category"))})
            except Exception:
                pass

    base_q = db.query(Product).filter(
        Product.is_deleted == False,   # noqa: E712
        Product.is_active == True,     # noqa: E712
        Product.is_approved == True,   # noqa: E712
    )

    if categories:
        results = (
            base_q
            .filter(Product.category.in_(categories))
            .order_by(Product.sales_count.desc())
            .limit(limit)
            .all()
        )
        if len(results) >= limit:
            return results
        # Top up with best sellers from other categories
        seen_ids = {p.id for p in results}
        fillers = (
            base_q
            .filter(Product.id.notin_(seen_ids))
            .order_by(Product.sales_count.desc())
            .limit(limit - len(results))
            .all()
        )
        return results + fillers

    return base_q.order_by(Product.sales_count.desc()).limit(limit).all()


# ── Cascade write functions for product deletion (moved from products_write_service) ───

def clear_product_carts(db: Session, product_id: int) -> int:
    """Remove (soft-delete) all cart items for a product during cascade delete."""
    from domains.governance.ports import CartItem
    return _soft_delete_by_product(db, CartItem, product_id)


def clear_product_wishlists(db: Session, product_id: int) -> int:
    """Remove (soft-delete) all wishlist items for a product during cascade delete."""
    from domains.catalog.models.products import WishlistItem
    return _soft_delete_by_product(db, WishlistItem, product_id)


def archive_product_reviews(db: Session, product_id: int) -> int:
    """Soft-delete a product's reviews, preserving the data history."""
    from domains.catalog.models.products import Review
    return _soft_delete_by_product(db, Review, product_id)


def _soft_delete_by_product(db: Session, model, product_id: int) -> int:
    """Soft-delete every (non-deleted) row of *model* for *product_id*."""
    from infrastructure.utils.datetime_utils import utcnow
    updated = (
        db.query(model)
        .filter(model.product_id == product_id, model.is_deleted.is_(False))
        .update(
            {model.is_deleted: True, model.deleted_at: utcnow()},
            synchronize_session=False,
        )
    )
    db.commit()
    return updated


def purge_product_cart_items(db: Session, product_id: int) -> int:
    """Remove every cart row referencing *product_id*. Caller commits."""
    from domains.governance.ports import CartItem
    return (
        db.query(CartItem)
        .filter(CartItem.product_id == product_id)
        .delete(synchronize_session=False)
    )


def purge_product_wishlist_items(db: Session, product_id: int) -> int:
    """Remove every wishlist row referencing *product_id*. Caller commits."""
    from domains.catalog.models.products import Wishlist
    return (
        db.query(Wishlist)
        .filter(Wishlist.product_id == product_id)
        .delete(synchronize_session=False)
    )


def soft_delete_product_reviews(db: Session, product_id: int) -> int:
    """Flag a product's live reviews as deleted. Caller commits."""
    from domains.catalog.models.products import Review
    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.is_deleted == False)
        .update({"is_deleted": True}, synchronize_session=False)
    )


def create_product_verification(
    db: Session,
    *,
    product_id: int,
    order_id: Optional[int] = None,
    shipment_id: Optional[int] = None,
    verified_by: Optional[int] = None,
    verification_type: Optional[str] = None,
    result: Optional[str] = None,
    expected_specs: Optional[str] = None,
    actual_specs: Optional[str] = None,
    discrepancies: Optional[str] = None,
    scan_code: Optional[str] = None,
    image_urls: Optional[str] = None,
    notes: Optional[str] = None,
):
    """Persist a new ProductVerification row and return it."""
    from domains.governance.models.admin import ProductVerification
    verification = ProductVerification(
        product_id=product_id,
        order_id=order_id,
        shipment_id=shipment_id,
        verified_by=verified_by,
        verification_type=verification_type,
        result=result,
        expected_specs=expected_specs,
        actual_specs=actual_specs,
        discrepancies=discrepancies,
        scan_code=scan_code,
        image_urls=image_urls,
        notes=notes,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def update_product_verification(db: Session, verification, updates: dict):
    """Apply *updates* to an existing verification row and return it."""
    for key, value in updates.items():
        setattr(verification, key, value)
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


# ── Admin Product Read Helpers (merged from product_admin_read_service.py) ───

def _bump_cache() -> None:
    _bump_product_cache_version()


def _scoped_product(db: Session, country_code: str, product_id: int) -> Product:
    """Resolve a product scoped to a country (404 + request RLS)."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        product = db.query(Product).filter(Product.id == product_id, Product.country_code == code).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    finally:
        clear_rls_context()


def list_products_paginated(
    db: Session,
    *,
    country_code: str,
    page: int,
    size: int,
    moderation_status: str | None = None,
    include_deleted: bool = False,
) -> dict:
    """Country-scoped, paginated product list used by the admin catalogue grid."""
    q = db.query(Product).filter(Product.country_code == country_code)
    if moderation_status:
        q = q.filter(Product.moderation_status == moderation_status)
    if not include_deleted:
        q = q.filter(Product.is_deleted == False)
    return paginated_response(q, page, size)


# ── Admin Product Write Helpers (merged from product_admin_write_service.py) ───

def approve_product_by_id(db: Session, country_code: str, product_id: int) -> dict:
    product = _scoped_product(db, country_code, product_id)
    product.moderation_status = "approved"
    product.is_verified = True
    db.commit()
    _bump_cache()
    return {"message": "Product approved"}


def reject_product_by_id(db: Session, country_code: str, product_id: int, reason: Optional[str] = None) -> dict:
    product = _scoped_product(db, country_code, product_id)
    product.moderation_status = "rejected"
    product.moderation_notes = reason
    db.commit()
    _bump_cache()
    return {"message": "Product rejected"}


def set_product_badge_by_id(db: Session, country_code: str, product_id: int, field: str, value: bool) -> dict:
    if field not in ("is_hot", "is_featured"):
        raise HTTPException(status_code=400, detail="field must be 'is_hot' or 'is_featured'")
    product = _scoped_product(db, country_code, product_id)
    setattr(product, field, value)
    db.commit()
    _bump_cache()
    return {"message": "Product badge updated", "field": field, "value": value}


# ── Product Domain Service (merged from product_service.py) ───

from typing import Mapping
from sqlalchemy.orm import Query
from domains.comms.models.suppliers import SupplierProfile
from infrastructure.utils.slug import generate_slug, generate_slug_hash


class ProductNotFoundError(LookupError):
    """Raised when a product does not exist or is not visible to the caller."""


