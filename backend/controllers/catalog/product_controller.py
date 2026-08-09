"""Catalog product controller (LAYER 3).

Orchestrates :mod:`services.catalog.product_service` for the public, supplier
and admin product surfaces, and converts service exceptions into HTTP errors.

This exists so routers never call the session. Every product write that used
to sit inline in ``routers/products.py``, ``routers/supplier_products.py`` and
``routers/admin_products.py`` (audit W1) now flows through here into the
service layer.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Query, Session

from data.models import Product, SupplierProfile
from services.catalog import product_service
from services.catalog.product_service import (
    ProductNotFoundError,
    SupplierProfileNotFoundError,
)
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "resolve_supplier_id",
    "get_supplier_products_query",
    "get_owned_product_or_404",
    "get_product_by_slug_hash_or_404",
    "get_country_products_query",
    "get_country_product_or_404",
    "create_product",
    "update_product_as_manager",
    "update_supplier_product",
    "update_product_discount",
    "replace_product_image",
    "soft_delete_product",
    "soft_delete_owned_product",
    "moderate_product",
    "set_product_badge",
    "build_discount_summary",
    "build_image_filename",
]


def _is_admin(user: Mapping[str, Any]) -> bool:
    return str((user or {}).get("role") or "").lower() == "admin"


# ── Supplier surface ──────────────────────────────────────────────────────────


def resolve_supplier_id(db: Session, user_id: int) -> int:
    """Return the supplier profile id for a user, or raise HTTP 404."""
    try:
        return int(product_service.get_supplier_profile(db, user_id).id)
    except SupplierProfileNotFoundError as exc:
        logger.exception("resolve_supplier_id_failed", error=str(exc))
        raise HTTPException(status_code=404, detail="Supplier profile not found") from exc


def get_supplier_products_query(db: Session, supplier_id: int) -> Query:
    """Paginatable query of a supplier's products."""
    return product_service.get_supplier_products_query(db, supplier_id)


def get_owned_product_or_404(
    db: Session,
    product_id: int,
    supplier_id: int,
    *,
    exclude_deleted: bool = False,
) -> Product:
    """Fetch a supplier-owned product or raise HTTP 404."""
    try:
        return product_service.get_owned_product(
            db, product_id, supplier_id, exclude_deleted=exclude_deleted
        )
    except ProductNotFoundError as exc:
        logger.exception("get_owned_product_or_404_failed", error=str(exc))
        raise HTTPException(status_code=404, detail="Product not found") from exc


def get_product_by_slug_hash_or_404(db: Session, slug_hash: str) -> Product:
    """Resolve a share-link hash to a product or raise HTTP 404."""
    product = product_service.get_product_by_slug_hash(db, slug_hash)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ── Admin / country surface ───────────────────────────────────────────────────


def get_country_products_query(
    db: Session,
    country_code: str,
    *,
    moderation_status: Optional[str] = None,
    include_deleted: bool = False,
) -> Query:
    """Admin product listing query scoped to a country."""
    return product_service.get_country_products_query(
        db,
        country_code,
        moderation_status=moderation_status,
        include_deleted=include_deleted,
    )


def get_country_product_or_404(db: Session, product_id: int, country_code: str) -> Product:
    """Fetch a country-scoped product or raise HTTP 404."""
    try:
        return product_service.get_country_product(db, product_id, country_code)
    except ProductNotFoundError as exc:
        logger.exception("get_country_product_or_404_failed", error=str(exc))
        raise HTTPException(status_code=404, detail="Product not found") from exc


# ── Writes ────────────────────────────────────────────────────────────────────


def create_product(
    db: Session,
    payload: Mapping[str, Any],
    current_user: Mapping[str, Any],
) -> Product:
    """Create a product on behalf of ``current_user``.

    A non-admin can only ever create products for themselves; the payload's
    ``supplier_id`` is ignored in that case.
    """
    data = dict(payload or {})
    actor_id = int(current_user["id"])

    if _is_admin(current_user):
        supplier_id = int(data.get("supplier_id") or actor_id)
    else:
        supplier_id = actor_id

    country_code = data.get("country_code") or current_user.get(
        "country_code"
    ) or current_user.get("preferred_country")
    if country_code:
        data["country_code"] = country_code

    try:
        return product_service.create_product(
            db,
            name=data.get("name"),
            supplier_id=supplier_id,
            payload=data,
            is_active=bool(data.get("is_active", True)),
            is_featured=bool(data.get("is_featured", False)),
            is_digital=bool(data.get("is_digital", False)),
        )
    except ValueError as exc:
        logger.exception("create_product_failed", error=str(exc))
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _assert_can_manage(product: Product, current_user: Mapping[str, Any]) -> None:
    if _is_admin(current_user):
        return
    if int(product.supplier_id or 0) != int(current_user["id"]):
        # 404 (not 403) so a probe cannot enumerate other suppliers' ids.
        raise HTTPException(status_code=404, detail="Product not found or not yours")


def update_product_as_manager(
    db: Session,
    product_id: int,
    payload: Mapping[str, Any],
    current_user: Mapping[str, Any],
) -> Product:
    """Admin/owner update of a product."""
    product = product_service.get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    _assert_can_manage(product, current_user)
    return product_service.update_product(db, product, payload)


def update_supplier_product(
    db: Session,
    product: Product,
    payload: Mapping[str, Any],
) -> Product:
    """Supplier-scoped product update (narrow field whitelist)."""
    return product_service.update_supplier_product(db, product, payload)


def _parse_discount_datetime(raw: Any, field: str) -> Optional[datetime]:
    if raw in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(raw)).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError) as exc:
        logger.exception("_parse_discount_datetime_failed", error=str(exc))
        raise HTTPException(
            status_code=400, detail=f"Invalid {field} format: {raw}"
        ) from exc


def update_product_discount(
    db: Session,
    product: Product,
    payload: Mapping[str, Any],
) -> Product:
    """Apply a discount payload (``clear``/``compare_price``/window) to a product."""
    data = dict(payload or {})

    if data.get("clear"):
        return product_service.update_product_discount(db, product, clear=True)

    compare_price: Any = ...
    if "compare_price" in data:
        raw = data["compare_price"]
        if raw is None:
            compare_price = None
        else:
            try:
                compare_price = float(raw)
            except (TypeError, ValueError) as exc:
                logger.exception("update_product_discount_failed", error=str(exc))
                raise HTTPException(
                    status_code=400, detail=f"Invalid compare_price: {raw}"
                ) from exc

    starts_at: Any = ...
    if "discount_starts_at" in data:
        starts_at = _parse_discount_datetime(
            data["discount_starts_at"], "discount_starts_at"
        )

    ends_at: Any = ...
    if "discount_ends_at" in data:
        ends_at = _parse_discount_datetime(data["discount_ends_at"], "discount_ends_at")

    return product_service.update_product_discount(
        db,
        product,
        compare_price=compare_price,
        discount_starts_at=starts_at,
        discount_ends_at=ends_at,
    )


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
    return f"product_{product_id}_{uuid.uuid4().hex[:8]}.{ext}"


def replace_product_image(db: Session, product: Product, image_url: str) -> Product:
    """Persist a product's new image URL."""
    return product_service.set_product_image(db, product, image_url)


def set_product_image_url(db: Session, product: Product, image_url: str) -> Product:
    """Persist a supplier-uploaded image URL (router owns storage I/O)."""
    return product_service.set_product_image(db, product, image_url)


def list_products_for_supplier(db: Session, supplier_id: int) -> Query:
    """Return the query of products owned by a supplier (for pagination)."""
    return product_service.list_products_for_supplier(db, supplier_id)


def get_supplier_product_or_404(
    db: Session, product_id: int, supplier_id: int
) -> Product:
    """Fetch a supplier-owned product or raise 404.

    Uses 404 (not 403) so a probe cannot enumerate other suppliers' ids.
    """
    product = product_service.get_supplier_product(db, product_id, supplier_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def get_supplier_profile_or_404(db: Session, user_id: int) -> SupplierProfile:
    """Resolve the supplier profile for a user, or raise 404."""
    profile = product_service.get_supplier_profile(db, user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Supplier profile not found")
    return profile


def list_country_products_query(
    db: Session,
    country_code: str,
    *,
    moderation_status: Optional[str] = None,
    include_deleted: bool = False,
) -> Query:
    """Country-scoped product query for the admin products list endpoint."""
    return product_service.list_country_products_query(
        db,
        country_code,
        moderation_status=moderation_status,
        include_deleted=include_deleted,
    )


def update_supplier_product_fields(
    db: Session, product: Product, payload: Mapping[str, Any]
) -> Product:
    """Supplier-scoped partial update of allow-listed basic fields."""
    return product_service.update_supplier_product(db, product, payload)


def discount_summary(db: Session, product: Product, now: datetime) -> dict[str, Any]:
    """Return the public discount projection dict for ``update_product_discount``."""
    return build_discount_summary(product, now)



def soft_delete_product(
    db: Session,
    product_id: int,
    current_user: Mapping[str, Any],
) -> Product:
    """Soft-delete a product the caller is allowed to manage."""
    product = product_service.get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    _assert_can_manage(product, current_user)
    return product_service.soft_delete_product(db, product)


def soft_delete_owned_product(db: Session, product: Product) -> Product:
    """Soft-delete an already-authorized supplier product."""
    return product_service.soft_delete_product(db, product, deactivate=False)


def moderate_product(
    db: Session,
    product: Product,
    status_value: str,
    *,
    notes: Optional[str] = None,
) -> Product:
    """Approve or reject a product listing."""
    try:
        return product_service.set_moderation_status(
            db, product, status_value, notes=notes
        )
    except ValueError as exc:
        logger.exception("moderate_product_failed", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def set_product_badge(db: Session, product: Product, field: str, value: bool) -> Product:
    """Toggle an ``is_hot`` / ``is_featured`` merchandising badge."""
    try:
        return product_service.set_product_badge(db, product, field, value)
    except ValueError as exc:
        logger.exception("set_product_badge_failed", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def set_product_verified(db: Session, product: Product, value: bool) -> Product:
    """Set/clear the ``is_verified`` trust flag on a product."""
    return product_service.set_product_verified(db, product, value)
