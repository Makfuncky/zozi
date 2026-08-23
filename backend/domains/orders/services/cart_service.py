"""Cart service — owns all server-cart read/write orchestration for authenticated users.

Layering contract (ARCHITECTURE_DIAGRAM.md §10):
    routers -> controllers -> services (this module) -> models

This module is the single source of truth for cart data access. It performs no
router/controller imports; variant resolution is a local pure helper so the
service layer stays free of cross-controller dependencies (avoids W4/DG cycles).
"""
from __future__ import annotations

import json
import logging
from typing import Any, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from infrastructure.database.schemas import (
    CartItemCreate,
    CartItemIn,
    CartItemViewOut,
    CartSyncRequest,
    CartViewOut,
    ProductCartViewOut,
)
from domains.governance.models.core import CartItem
from domains.catalog.models.products import Product
from domains.orders.services.cart_write_service import create_cart_item
from domains.orders.services.cart_write_service import delete_cart_items_by_user
from domains.orders.services.cart_write_service import get_active_product_by_id
from domains.orders.services.cart_write_service import get_cart_item_by_variant
from domains.orders.services.cart_write_service import get_products_by_ids
from domains.orders.services.cart_write_service import load_cart_items
from domains.orders.services.cart_write_service import update_cart_item as write_update_cart_item
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


# ── Variant resolution (local pure helper; no controller import) ───────────────

def _normalize_variant_selector(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _resolve_variant(product: Product, selected_size: Optional[str], selected_color: Optional[str]) -> Optional[Any]:
    variants = list(getattr(product, "variants", []) or [])
    if not variants:
        return None

    normalized_size = _normalize_variant_selector(selected_size)
    normalized_color = _normalize_variant_selector(selected_color)
    if not normalized_size and not normalized_color:
        return None

    def _attribute_values(variant: Any) -> List[str]:
        raw = getattr(variant, "attributes_json", None)
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            logger.exception("_attribute_values_failed", error=str(e))
            return []
        if not isinstance(parsed, dict):
            return []
        return [str(value).strip().lower() for value in parsed.values() if str(value).strip()]

    for variant in variants:
        if not getattr(variant, "is_active", True):
            continue
        variant_size = _normalize_variant_selector(getattr(variant, "size", None))
        variant_color = _normalize_variant_selector(getattr(variant, "color", None))
        variant_title = _normalize_variant_selector(getattr(variant, "title", None))
        attribute_values = _attribute_values(variant)

        color_matches = not normalized_color or normalized_color == variant_color or normalized_color in attribute_values
        size_matches = not normalized_size or normalized_size in {variant_size, variant_title} or normalized_size in attribute_values
        if color_matches and size_matches:
            return variant

    return None


def _resolve_variant_or_raise(product: Product, selected_size: Optional[str], selected_color: Optional[str]) -> Optional[Any]:
    variant = _resolve_variant(product, selected_size, selected_color)
    has_variants = bool(getattr(product, "variants", []) or [])
    if has_variants and (_normalize_variant_selector(selected_size) or _normalize_variant_selector(selected_color)) and variant is None:
        raise HTTPException(status_code=422, detail="Selected variant is not available for this product")
    return variant


def _variant_key(product_id: int, selected_size: Optional[str], selected_color: Optional[str]) -> tuple[int, str, str]:
    return (product_id, (selected_size or "").strip(), (selected_color or "").strip())


# ── Serialization (preserves the exact router response contract) ───────────────

def _serialize_cart_item(item: CartItem) -> dict:
    product = item.product
    selected_size = getattr(item, "selected_size", None) or ""
    selected_color = getattr(item, "selected_color", None) or ""
    variant_requested = bool(selected_size.strip() or selected_color.strip())
    variant = _resolve_variant(product, selected_size, selected_color) if product else None

    if product is None:
        available_stock = 0
        is_available = False
        availability_reason = "Product is no longer available."
    elif variant_requested and variant is None:
        available_stock = 0
        is_available = False
        availability_reason = "Selected variant is no longer available."
    else:
        available_stock = int(getattr(variant, "stock", getattr(product, "stock", 0)) or 0)
        is_active = bool(getattr(product, "is_active", True))
        is_available = is_active and available_stock > 0
        if not is_active:
            availability_reason = "Product is no longer available."
        elif available_stock <= 0:
            availability_reason = "This item is out of stock. Remove it to continue."
        elif item.quantity > available_stock:
            availability_reason = f"Only {available_stock} left in stock. Reduce the quantity to continue."
        else:
            availability_reason = None

    return {
        "id": item.id,
        "product_id": item.product_id,
        "product_name": product.name if product else "",
        "image_url": product.image_url if product else None,
        "price": float(product.price) if product else 0.0,
        "quantity": item.quantity,
        "selected_size": selected_size,
        "selected_color": item.selected_color,
        "available_stock": available_stock,
        "is_available": is_available,
        "availability_reason": availability_reason,
        "product": {
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "image_url": product.image_url,
        } if product else None,
    }


# ── Reads ──────────────────────────────────────────────────────────────────────

def get_cart(user_id: int, db: Session) -> CartViewOut:
    items = load_cart_items(db, user_id)
    normalized = [_serialize_cart_item(i) for i in items]
    subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))
    return CartViewOut(items=normalized, subtotal=subtotal, item_count=len(normalized))


# ── Writes ─────────────────────────────────────────────────────────────────────

def _find_item(db: Session, product_id: int, user_id: int) -> Optional[CartItem]:
    """Mirror the historical router lookup: try cart-item id, then product id."""
    item = db.query(CartItem).filter(CartItem.id == product_id, CartItem.user_id == user_id).first()
    if item is None:
        item = db.query(CartItem).filter(CartItem.product_id == product_id, CartItem.user_id == user_id).first()
    return item


def add_to_cart(user_id: int, payload: CartItemCreate, db: Session) -> dict:
    product = get_active_product_by_id(db, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    selected_size = payload.selected_size or ""
    selected_color = payload.selected_color or ""
    existing = get_cart_item_by_variant(db, user_id, payload.product_id, selected_size, selected_color)
    if existing:
        existing.quantity += payload.quantity
        write_update_cart_item(db, existing, {"quantity": existing.quantity})
    else:
        create_cart_item(
            db,
            user_id=user_id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            quantity=payload.quantity,
            selected_size=selected_size,
            selected_color=selected_color,
        )
    return {"message": "Added to cart"}


def update_cart_item(
    user_id: int,
    product_id: int,
    quantity: int,
    selected_size: str,
    selected_color: str,
    db: Session,
) -> dict:
    item = _find_item(db, product_id, user_id)
    if not item:
        product = get_active_product_by_id(db, product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        if quantity > 0:
            create_cart_item(db, user_id=user_id, product_id=product_id, quantity=quantity)
        return {"message": "Updated"}
    if quantity <= 0:
        db.delete(item)
        db.commit()
    else:
        item.quantity = quantity
        write_update_cart_item(db, item, {"quantity": quantity})
    return {"message": "Updated"}


def remove_cart_item(user_id: int, product_id: int, db: Session) -> dict:
    item = _find_item(db, product_id, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Removed"}


def clear_cart(user_id: int, db: Session) -> dict:
    delete_cart_items_by_user(db, user_id)
    return {"message": "Cart cleared"}


def sync_cart(user_id: int, body: CartSyncRequest, db: Session) -> CartViewOut:
    """Bulk-replace the server cart with the supplied items (login sync).

    Server items not present in the incoming list are removed; incoming items
    replace quantities (client wins on login sync).
    """
    if not body.items:
        delete_cart_items_by_user(db, user_id)
        return CartViewOut(items=[], subtotal=0.0, item_count=0)

    product_ids = sorted({item.product_id for item in body.items})
    products = {p.id: p for p in get_products_by_ids(db, product_ids)}

    normalized_items = {
        _variant_key(item.product_id, item.selected_size, item.selected_color): item
        for item in body.items
    }
    incoming_keys = set(normalized_items.keys())

    existing_items = load_cart_items(db, user_id)
    existing_by_key = {
        _variant_key(i.product_id, i.selected_size, i.selected_color): i
        for i in existing_items
    }

    for existing in existing_items:
        key = _variant_key(existing.product_id, existing.selected_size, existing.selected_color)
        if key not in incoming_keys:
            db.delete(existing)
            db.commit()

    for variant_key, item in normalized_items.items():
        if item.product_id not in products:
            continue
        qty = max(1, min(item.quantity, 999))
        _, selected_size, selected_color = variant_key
        variant = _resolve_variant_or_raise(products[item.product_id], selected_size, selected_color)
        available_stock = int(getattr(variant, "stock", products[item.product_id].stock))
        if available_stock < qty:
            raise HTTPException(status_code=409, detail="Insufficient stock for one of the selected products")
        existing = existing_by_key.get(variant_key)
        if existing:
            existing.quantity = qty
            write_update_cart_item(db, existing, {"quantity": qty})
        else:
            create_cart_item(
                db,
                user_id=user_id,
                product_id=item.product_id,
                quantity=qty,
                selected_size=selected_size,
                selected_color=selected_color,
            )

    return get_cart(user_id, db)
