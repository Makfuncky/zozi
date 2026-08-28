"""Cart service — owns all server-cart read/write orchestration for authenticated users.

Layering contract (ARCHITECTURE_DIAGRAM.md §10):
    routers -> controllers -> services (this module) -> models

This module is the single source of truth for cart data access. It performs no
router/controller imports; variant resolution is a local pure helper so the
service layer stays free of cross-controller dependencies (avoids W4/DG cycles).

Merged from: cart_service.py, cart_legacy_service.py, cart_write_service.py
"""
from __future__ import annotations

import json
import logging
from typing import Any, List, Optional

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload, selectinload

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
from domains.catalog.ports import resolve_product_variant
from domains.logistics.ports import quote_shipping_for_destination
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
from infrastructure.utils.config import settings
from infrastructure.utils.performance_cache import cache_cart, set_cart, invalidate_cart
import structlog

logger = structlog.get_logger(__name__)
logger = logging.getLogger(__name__)

_CART_CACHE_TTL = 60  # 1 minute - carts change frequently


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CartShippingQuoteRequest(BaseModel):
    country: str
    city: str = ""
    subtotal: float = 0.0
    total_weight_kg: float = 0.0
    pickup_count: int | None = None
    dropoff_count: int | None = None
    items: List[CartItemIn] = []


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
    # Check cache first
    cached_cart = cache_cart(user_id)
    if cached_cart is not None:
        return CartViewOut(**cached_cart)

    items = load_cart_items(db, user_id)
    normalized = [_serialize_cart_item(i) for i in items]
    subtotal = float(sum(i["price"] * i["quantity"] for i in normalized))
    result = CartViewOut(items=normalized, subtotal=subtotal, item_count=len(normalized))

    # Cache the cart
    set_cart(user_id, result.model_dump(), ttl=_CART_CACHE_TTL)
    return result


def get_cart_legacy(user_id: int, db: Session) -> List[dict]:
    """Legacy cart read — returns raw list of cart rows with product snapshots."""
    items = load_cart_items(db, user_id)
    return [_cart_row(i) for i in items if i.product and not i.product.is_deleted]


def _product_snapshot(p: Product, selected_size: str | None = None, selected_color: str | None = None) -> dict:
    """Return the minimal product fields needed to render a cart row."""
    variant = resolve_product_variant(p, selected_size, selected_color)
    return {
        "id": p.id,
        "name": p.name,
        "price": variant.price if variant and variant.price is not None else p.price,
        "image_url": variant.media_url if variant and variant.media_url else p.image_url,
        "stock": variant.stock if variant else p.stock,
        "category": p.category,
        "weight": p.weight,
        "is_active": p.is_active,
        "is_deleted": p.is_deleted,
        "variant_title": variant.title if variant else None,
        "variant_sku": variant.sku if variant else None,
        "variant_barcode": variant.barcode if variant else None,
        "variant_product_code": variant.product_code if variant else None,
    }


def _cart_row(item: CartItem) -> dict[str, Any]:
    snapshot: dict[str, Any] = _product_snapshot(item.product, item.selected_size, item.selected_color) if item.product else {"id": item.product_id}
    snapshot["quantity"] = item.quantity
    snapshot["cart_item_id"] = item.id
    snapshot["selected_size"] = item.selected_size or ""
    snapshot["selected_color"] = item.selected_color or ""
    return snapshot


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
    invalidate_cart(user_id)
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
        invalidate_cart(user_id)
        return {"message": "Updated"}
    if quantity <= 0:
        db.delete(item)
        db.commit()
    else:
        item.quantity = quantity
        write_update_cart_item(db, item, {"quantity": quantity})
    invalidate_cart(user_id)
    return {"message": "Updated"}


def remove_cart_item(user_id: int, product_id: int, db: Session) -> dict:
    item = _find_item(db, product_id, user_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    invalidate_cart(user_id)
    return {"message": "Removed"}


def remove_cart_item_by_variant(user_id: int, product_id: int, selected_size: str | None, selected_color: str | None, db: Session) -> List[dict]:
    """Remove cart item by variant (legacy signature)."""
    db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == product_id,
        CartItem.selected_size == (selected_size or "").strip(),
        CartItem.selected_color == (selected_color or "").strip(),
    ).delete()
    db.commit()
    return get_cart_legacy(user_id, db)


def clear_cart(user_id: int, db: Session) -> dict:
    delete_cart_items_by_user(db, user_id)
    invalidate_cart(user_id)
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


def upsert_cart_item_legacy(user_id: int, product_id: int, quantity: int, selected_size: str | None, selected_color: str | None, db: Session) -> List[dict]:
    """Add or update a single item in the server cart (legacy signature)."""
    if quantity <= 0:
        return remove_cart_item_by_variant(user_id, product_id, selected_size, selected_color, db)

    product = db.query(Product).options(selectinload(Product.variants)).filter(
        Product.id == product_id,
        Product.is_deleted.is_(False),
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    qty = max(1, min(quantity, 999))
    normalized_size = (selected_size or "").strip()
    normalized_color = (selected_color or "").strip()
    variant = _resolve_variant_or_raise(product, normalized_size, normalized_color)
    available_stock = int(getattr(variant, "stock", product.stock))
    if available_stock < qty:
        raise HTTPException(status_code=409, detail=f"Insufficient stock for '{product.name}'")

    existing = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id,
            CartItem.selected_size == normalized_size,
            CartItem.selected_color == normalized_color,
        )
        .first()
    )
    if existing:
        existing.quantity = qty
    else:
        db.add(
            CartItem(
                user_id=user_id,
                product_id=product_id,
                quantity=qty,
                selected_size=normalized_size,
                selected_color=normalized_color,
            )
        )

    db.commit()
    return get_cart_legacy(user_id, db)


def get_cart_shipping_quote(body: CartShippingQuoteRequest, db: Session) -> dict[str, Any]:
    """Compute a shipping quote for the current cart contents."""
    import domains.orders.services.orders_service as orders_ctrl
    from infrastructure.database.schemas import OrderCreate

    country = body.country.strip()
    city = body.city.strip()
    if not country:
        raise HTTPException(status_code=422, detail="country is required")

    if body.items:
        preview_items = [item.model_dump() if isinstance(item, BaseModel) else item for item in body.items]
        preview_order = OrderCreate(
            items=preview_items,
            country=country,
            city=city or None,
            shipping_address=None,
            save_to_profile=False,
        )
        products, _ = orders_ctrl._load_products_for_order(preview_order, db)
        supplier_totals = orders_ctrl._group_supplier_totals(preview_order, products, db)
        if supplier_totals:
            shipping_amount, shipment_groups = orders_ctrl._quote_supplier_groups(
                supplier_totals=supplier_totals,
                destination_country=country,
                destination_city=city,
                db=db,
            )
            partner_id, _, estimated_delivery_min, estimated_delivery_max = orders_ctrl._resolve_order_level_logistics_fields(shipment_groups)
            partner_name = None
            if partner_id is not None:
                matching_quote = next((quote for quote in shipment_groups if quote.get("partner_id") == partner_id), None)
                partner_name = matching_quote.get("partner_name") if matching_quote else None
            return {
                "shipping_amount": float(shipping_amount),
                "currency": settings.default_currency,
                "partner_id": partner_id,
                "partner_name": partner_name,
                "partner_code": None,
                "estimated_delivery_min": estimated_delivery_min,
                "estimated_delivery_max": estimated_delivery_max,
                "source": "shipment_groups" if len(shipment_groups) > 1 else str(shipment_groups[0].get("source") or "fallback"),
                "shipment_groups": shipment_groups,
            }

    partner_quote = quote_shipping_for_destination(
        db,
        country=country,
        city=city,
        total_weight_kg=max(0.0, float(body.total_weight_kg or 0)),
        pickup_count=body.pickup_count,
        dropoff_count=body.dropoff_count,
    )
    if partner_quote is not None:
        sa = partner_quote.get("service_area") or {}
        return {
            **partner_quote,
            "source": "approved_logistics_partner",
            "estimated_delivery_min": sa.get("delivery_days_min"),
            "estimated_delivery_max": sa.get("delivery_days_max"),
        }

    subtotal = max(0.0, float(body.subtotal or 0))
    free_threshold = float(getattr(settings, "free_shipping_threshold", 0) or 0)
    flat_rate = float(getattr(settings, "shipping_flat_rate", 0) or 0)
    shipping_amount = 0.0 if free_threshold > 0 and subtotal >= free_threshold else flat_rate
    return {
        "shipping_amount": round(shipping_amount, 2),
        "currency": "AED",
        "partner_id": None,
        "partner_name": None,
        "partner_code": None,
        "service_area": None,
        "pricing_breakdown": None,
        "destination": {
            "country": country,
            "country_code": "",
            "city": city or None,
            "city_key": "",
        },
        "source": "fallback",
        "estimated_delivery_min": None,
        "estimated_delivery_max": None,
    }


# ── DB write operations ────────────────────────────────────────────────────────

def load_cart_items(db: Session, user_id: int) -> list[CartItem]:
    """Return all cart items for *user_id* with product + variants preloaded."""
    return (
        db.query(CartItem)
        .options(joinedload(CartItem.product).selectinload(Product.variants))
        .filter(CartItem.user_id == user_id)
        .limit(SAFE_QUERY_LIMIT).all()
    )


def get_products_by_ids(db: Session, product_ids: list[int]) -> list[Product]:
    """Return non-deleted products with variants preloaded for the given IDs."""
    return (
        db.query(Product)
        .options(selectinload(Product.variants))
        .filter(
            Product.id.in_(product_ids),
            Product.is_deleted.is_(False),
        )
        .limit(SAFE_QUERY_LIMIT).all()
    )


def get_active_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Return a non-deleted product with variants preloaded, or None."""
    return (
        db.query(Product)
        .options(selectinload(Product.variants))
        .filter(
            Product.id == product_id,
            Product.is_deleted.is_(False),
        )
        .first()
    )


def get_cart_item_by_variant(
    db: Session,
    user_id: int,
    product_id: int,
    selected_size: str,
    selected_color: str,
) -> Optional[CartItem]:
    """Return a single cart item matching the given variant, or None."""
    return (
        db.query(CartItem)
        .filter(
            CartItem.user_id == user_id,
            CartItem.product_id == product_id,
            CartItem.selected_size == selected_size,
            CartItem.selected_color == selected_color,
        )
        .first()
    )


def create_cart_item(db: Session, **item_data) -> CartItem:
    item = CartItem(**item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def write_update_cart_item(db: Session, item: CartItem, updates: dict) -> CartItem:
    """DB-level cart item update (row writer)."""
    for key, value in updates.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


def delete_cart_item(db: Session, item: CartItem) -> None:
    db.delete(item)
    db.commit()


def delete_cart_item_by_variant(
    db: Session,
    user_id: int,
    product_id: int,
    selected_size: str | None,
    selected_color: str | None,
) -> None:
    normalized_size = (selected_size or "").strip()
    normalized_color = (selected_color or "").strip()
    db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == product_id,
        CartItem.selected_size == normalized_size,
        CartItem.selected_color == normalized_color,
    ).delete(synchronize_session=False)
    db.commit()


def delete_cart_items_by_user(db: Session, user_id: int) -> None:
    db.query(CartItem).filter(CartItem.user_id == user_id).delete(synchronize_session=False)
    db.commit()


def delete_cart_items_by_filter(db: Session, filters) -> None:
    db.query(CartItem).filter(filters).delete()
    db.commit()


def commit_cart_items(db: Session) -> None:
    db.commit()


def upsert_cart_item(
    db: Session,
    user_id: int,
    product_id: int,
    quantity: int,
    selected_size: str,
    selected_color: str,
    existing: CartItem | None = None,
) -> CartItem:
    if existing:
        existing.quantity = quantity
        db.commit()
        db.refresh(existing)
        return existing
    else:
        item = CartItem(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            selected_size=selected_size,
            selected_color=selected_color,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


def sync_cart_items(
    db: Session,
    user_id: int,
    actions: list[dict],
) -> None:
    """Apply a list of add/update/delete actions for cart items."""
    for action in actions:
        op = action.get("op")
        if op == "delete":
            item = action.get("item")
            if item:
                db.delete(item)
        elif op == "upsert":
            item = action.get("item")
            if item:
                db.add(item)
    db.commit()
