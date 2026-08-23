"""Product domain service (LAYER 4).

Owns every write against ``commerce.products`` plus the ownership/scoping
reads those writes depend on. Routers (Layer 2) and controllers (Layer 3) must
call these functions instead of using the session directly — that is what
clears the LC1 (layer contract) and W1 (controller/router DB write) findings
for the catalog module.

Design notes
------------
* Every mutator returns the refreshed ORM instance so the caller can serialize
  it without a second round-trip.
* Field whitelists (``_CREATE_FIELDS`` / ``_UPDATE_FIELDS`` /
  ``_SUPPLIER_UPDATE_FIELDS``) prevent mass-assignment: a client cannot flip
  ``is_verified`` or ``supplier_id`` through a generic update payload.
* Slug uniqueness is resolved here, once, instead of being re-implemented in
  each router.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Query, Session

from domains.catalog.models.products import Product
from domains.comms.models.suppliers import SupplierProfile
from infrastructure.utils.slug import generate_slug, generate_slug_hash
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)

MODERATION_APPROVED = "approved"
MODERATION_REJECTED = "rejected"
MODERATION_PENDING = "pending"

#: Badge flags an admin is allowed to toggle via the badge endpoint.
BADGE_FIELDS: frozenset[str] = frozenset({"is_hot", "is_featured"})

#: Fields accepted when creating a product.
_CREATE_FIELDS: frozenset[str] = frozenset(
    {
        "description",
        "short_description",
        "sku",
        "barcode",
        "price",
        "compare_price",
        "cost_price",
        "stock",
        "low_stock_threshold",
        "weight",
        "dimensions",
        "image_url",
        "images",
        "category",
        "subcategory",
        "category_id",
        "tags",
        "attributes",
        "brand",
        "color",
        "sizes",
        "materials",
        "meta_title",
        "meta_description",
        "country_code",
    }
)

#: Fields an admin/owner may change on an existing product.
_UPDATE_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "description",
        "short_description",
        "price",
        "compare_price",
        "cost_price",
        "stock",
        "low_stock_threshold",
        "weight",
        "dimensions",
        "image_url",
        "images",
        "category",
        "subcategory",
        "category_id",
        "tags",
        "attributes",
        "is_active",
        "is_featured",
        "brand",
        "color",
        "sizes",
        "materials",
        "rating",
        "meta_title",
        "meta_description",
    }
)

#: Narrower whitelist for the supplier surface.
_SUPPLIER_UPDATE_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "description",
        "price",
        "stock",
        "category",
        "is_active",
        "tags",
        "image_url",
    }
)

#: Payload aliases -> canonical column names.
_FIELD_ALIASES: dict[str, str] = {"stock_quantity": "stock"}

__all__ = [
    "MODERATION_APPROVED",
    "MODERATION_REJECTED",
    "MODERATION_PENDING",
    "BADGE_FIELDS",
    "ProductNotFoundError",
    "SupplierProfileNotFoundError",
    "unique_slug",
    "get_product_by_id",
    "get_product_by_slug_hash",
    "get_supplier_profile",
    "get_supplier_products_query",
    "get_owned_product",
    "get_country_products_query",
    "get_country_product",
    "create_product",
    "update_product",
    "update_supplier_product",
    "update_product_discount",
    "set_product_image",
    "soft_delete_product",
    "set_moderation_status",
    "set_product_badge",
]


class ProductNotFoundError(LookupError):
    """Raised when a product does not exist or is not visible to the caller."""


class SupplierProfileNotFoundError(LookupError):
    """Raised when the acting user has no supplier profile."""


# ── Helpers ───────────────────────────────────────────────────────────────────


def _normalize(payload: Mapping[str, Any], allowed: frozenset[str]) -> dict[str, Any]:
    """Resolve aliases and drop any key outside ``allowed``."""
    resolved: dict[str, Any] = {}
    for key, value in (payload or {}).items():
        canonical = _FIELD_ALIASES.get(key, key)
        if canonical in allowed:
            resolved[canonical] = value
    return resolved


def unique_slug(db: Session, name: str) -> str:
    """Return a slug for ``name`` that no other product currently holds."""
    base = generate_slug(name)
    slug = base
    counter = 1
    while db.query(Product.id).filter(Product.slug == slug).first() is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug


# ── Reads ─────────────────────────────────────────────────────────────────────


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Fetch a product by primary key."""
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_by_slug_hash(db: Session, slug_hash: str) -> Optional[Product]:
    """Fetch a product by its short share-link hash."""
    return db.query(Product).filter(Product.slug_hash == slug_hash).first()


def get_supplier_profile(db: Session, user_id: int) -> SupplierProfile:
    """Return the supplier profile for ``user_id``.

    Raises:
        SupplierProfileNotFoundError: when the user has no supplier profile.
    """
    profile = (
        db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    )
    if profile is None:
        raise SupplierProfileNotFoundError("Supplier profile not found")
    return profile


def get_supplier_products_query(db: Session, supplier_id: int) -> Query:
    """Query of every product owned by ``supplier_id`` (newest first)."""
    return (
        db.query(Product)
        .filter(Product.supplier_id == supplier_id)
        .order_by(Product.id.desc())
    )


def list_products_for_supplier(db: Session, supplier_id: int) -> Query:
    """Alias used by the supplier products router for pagination."""
    return get_supplier_products_query(db, supplier_id)


def get_supplier_product(
    db: Session, product_id: int, supplier_id: int
) -> Optional[Product]:
    """Fetch a single product owned by ``supplier_id`` (may be ``None``)."""
    return (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier_id)
        .first()
    )


def get_owned_product(
    db: Session,
    product_id: int,
    supplier_id: int,
    *,
    exclude_deleted: bool = False,
) -> Product:
    """Fetch a product, asserting the supplier owns it.

    Raises:
        ProductNotFoundError: when missing or owned by somebody else.
    """
    query = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == supplier_id,
    )
    if exclude_deleted:
        query = query.filter(Product.is_deleted.is_(False))
    product = query.first()
    if product is None:
        raise ProductNotFoundError("Product not found")
    return product


def get_country_products_query(
    db: Session,
    country_code: str,
    *,
    moderation_status: Optional[str] = None,
    include_deleted: bool = False,
) -> Query:
    """Admin listing query scoped to one country."""
    query = db.query(Product).filter(Product.country_code == country_code.upper())
    if moderation_status:
        query = query.filter(Product.moderation_status == moderation_status)
    if not include_deleted:
        query = query.filter(Product.is_deleted.is_(False))
    return query.order_by(Product.id.desc())


def list_country_products_query(
    db: Session,
    country_code: str,
    *,
    moderation_status: Optional[str] = None,
    include_deleted: bool = False,
) -> Query:
    """Country-scoped ordered product query for the admin list endpoint."""
    query = (
        db.query(Product)
        .filter(Product.country_code == country_code.upper())
        .order_by(Product.id.desc())
    )
    if moderation_status:
        query = query.filter(Product.moderation_status == moderation_status)
    if not include_deleted:
        query = query.filter(Product.is_deleted == False)  # noqa: E712
    return query


def get_country_product(db: Session, product_id: int, country_code: str) -> Product:
    """Fetch a product inside a country scope.

    Raises:
        ProductNotFoundError: when missing in that country.
    """
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.country_code == country_code.upper(),
        )
        .first()
    )
    if product is None:
        raise ProductNotFoundError("Product not found")
    return product


# ── Writes ────────────────────────────────────────────────────────────────────


def create_product(
    db: Session,
    *,
    name: str,
    supplier_id: int,
    payload: Optional[Mapping[str, Any]] = None,
    is_active: bool = True,
    is_featured: bool = False,
    is_digital: bool = False,
    is_verified: bool = True,
    is_approved: bool = True,
    moderation_status: str = MODERATION_APPROVED,
) -> Product:
    """Create a product owned by ``supplier_id``.

    Trust flags (``is_verified`` / ``is_approved`` / ``moderation_status``) are
    explicit keyword arguments rather than payload keys, so an untrusted body
    can never self-approve a listing.

    Raises:
        ValueError: when ``name`` is blank.
    """
    clean_name = str(name or "").strip()
    if not clean_name:
        raise ValueError("Product name is required")

    data = _normalize(payload or {}, _CREATE_FIELDS)

    product = Product(
        name=clean_name,
        slug=unique_slug(db, clean_name),
        slug_hash=generate_slug_hash(clean_name),
        supplier_id=int(supplier_id),
        price=data.pop("price", None) or 0,
        stock=data.pop("stock", None) or 0,
        low_stock_threshold=data.pop("low_stock_threshold", None) or 5,
        rating=float(data.pop("rating", 0.0) or 0.0),
        is_active=bool(is_active),
        is_featured=bool(is_featured),
        is_digital=bool(is_digital),
        is_verified=bool(is_verified),
        is_approved=bool(is_approved),
        is_deleted=False,
        moderation_status=str(moderation_status or MODERATION_APPROVED),
    )
    for field, value in data.items():
        setattr(product, field, value)

    db.add(product)
    db.commit()
    db.refresh(product)
    logger.info("product.created id=%s supplier_id=%s", product.id, supplier_id)
    return product


def update_product(
    db: Session,
    product: Product,
    updates: Mapping[str, Any],
    *,
    allowed_fields: Optional[frozenset[str]] = None,
    regenerate_slug: bool = True,
) -> Product:
    """Apply whitelisted ``updates`` to ``product`` and persist them."""
    data = _normalize(updates, allowed_fields or _UPDATE_FIELDS)

    for field, value in data.items():
        setattr(product, field, value)

    if regenerate_slug and data.get("name"):
        product.slug = unique_slug(db, str(data["name"]))

    db.commit()
    db.refresh(product)
    logger.info("product.updated id=%s fields=%s", product.id, sorted(data))
    return product


def update_supplier_product(
    db: Session,
    product: Product,
    updates: Mapping[str, Any],
) -> Product:
    """Supplier-surface update using the narrower field whitelist."""
    return update_product(
        db,
        product,
        updates,
        allowed_fields=_SUPPLIER_UPDATE_FIELDS,
        regenerate_slug=False,
    )


def update_product_discount(
    db: Session,
    product: Product,
    *,
    clear: bool = False,
    compare_price: Any = ...,
    discount_starts_at: Any = ...,
    discount_ends_at: Any = ...,
) -> Product:
    """Set or clear the discount window on a product.

    ``...`` (Ellipsis) is used as the "not supplied" sentinel so an explicit
    ``None`` can still clear an individual field.
    """
    if clear:
        product.compare_price = None
        product.discount_starts_at = None
        product.discount_ends_at = None
        db.commit()
        db.refresh(product)
        logger.info("product.discount_cleared id=%s", product.id)
        return product

    if compare_price is not ...:
        product.compare_price = (
            float(compare_price) if compare_price is not None else None
        )
    if discount_starts_at is not ...:
        product.discount_starts_at = discount_starts_at
    if discount_ends_at is not ...:
        product.discount_ends_at = discount_ends_at

    db.commit()
    db.refresh(product)
    logger.info("product.discount_updated id=%s", product.id)
    return product


def set_product_image(db: Session, product: Product, image_url: str) -> Product:
    """Point a product at a newly uploaded image."""
    product.image_url = image_url
    db.commit()
    db.refresh(product)
    logger.info("product.image_updated id=%s", product.id)
    return product


def soft_delete_product(
    db: Session,
    product: Product,
    *,
    deactivate: bool = True,
) -> Product:
    """Soft-delete a product (``is_deleted=True``, optionally ``is_active=False``)."""
    product.is_deleted = True
    if deactivate:
        product.is_active = False
    db.commit()
    db.refresh(product)
    logger.info("product.soft_deleted id=%s", product.id)
    return product


def set_moderation_status(
    db: Session,
    product: Product,
    status: str,
    *,
    notes: Optional[str] = None,
) -> Product:
    """Approve or reject a product listing.

    Raises:
        ValueError: when ``status`` is not a known moderation state.
    """
    normalized = str(status or "").lower()
    if normalized not in {
        MODERATION_APPROVED,
        MODERATION_REJECTED,
        MODERATION_PENDING,
    }:
        raise ValueError(f"Unsupported moderation status: {status!r}")

    product.moderation_status = normalized
    if normalized == MODERATION_APPROVED:
        product.is_verified = True
    if notes is not None and hasattr(product, "moderation_notes"):
        product.moderation_notes = notes

    db.commit()
    db.refresh(product)
    logger.info("product.moderated id=%s status=%s", product.id, normalized)
    return product


def set_product_badge(db: Session, product: Product, field: str, value: bool) -> Product:
    """Toggle a merchandising badge flag.

    Raises:
        ValueError: when ``field`` is not an allowed badge column.
    """
    if field not in BADGE_FIELDS:
        raise ValueError(f"field must be one of {sorted(BADGE_FIELDS)}")

    setattr(product, field, bool(value))
    db.commit()
    db.refresh(product)
    logger.info("product.badge_updated id=%s field=%s value=%s", product.id, field, value)
    return product


def set_product_verified(db: Session, product: Product, value: bool) -> Product:
    """Set/clear the ``is_verified`` trust flag."""
    product.is_verified = bool(value)
    db.commit()
    db.refresh(product)
    logger.info("product.verified id=%s value=%s", product.id, value)
    return product


# ── Helpers relocated from the deprecated controllers.catalog.product_controller ──

def _parse_discount_datetime(raw: Any, field: str) -> Optional[datetime]:
    """Parse an ISO-8601 discount-window timestamp, raising a 400 on bad input."""
    if raw in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(raw)).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError) as exc:
        logger.exception("_parse_discount_datetime_failed", error=str(exc))
        raise HTTPException(
            status_code=400, detail=f"Invalid {field} format: {raw}"
        ) from exc


def build_discount_summary(product: Product, now: datetime) -> dict[str, Any]:
    """Compute the public discount projection for a product."""
    price = float(product.price or 0)
    compare_price = (
        float(product.compare_price) if product.compare_price is not None else None
    )

    discount_pct = 0.0
    if compare_price and compare_price > 0:
        discount_pct = round((1 - price / compare_price) * 100, 1)

    active = bool(compare_price and compare_price > price)
    starts_at = product.discount_starts_at
    ends_at = product.discount_ends_at
    if starts_at and ends_at:
        active = active and starts_at <= now <= ends_at
    elif starts_at:
        active = active and starts_at <= now

    return {
        "product_id": product.id,
        "price": price,
        "compare_price": compare_price,
        "discount_percentage": discount_pct,
        "discount_active": active,
    }


def build_image_filename(product_id: int, original_filename: Optional[str]) -> str:
    """Derive a collision-free storage filename for a product image."""
    name = original_filename or "product.jpg"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else "jpg"
    return f"product_{product_id}_{uuid4().hex[:8]}.{ext}"
