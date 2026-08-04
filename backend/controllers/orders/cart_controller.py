"""Variant-aware server-side cart for authenticated users."""
from typing import Any, List, cast

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.orders.cart_shipping_service import (
    _load_products_for_order,
    _group_supplier_totals,
    _quote_supplier_groups,
    _resolve_order_level_logistics_fields,
)
from services.commerce.cart_write_service import (
    delete_cart_items_by_user,
    delete_cart_item_by_variant,
    upsert_cart_item,
    sync_cart_items,
    load_cart_items,
    get_products_by_ids,
    get_active_product_by_id,
    get_cart_item_by_variant,
)
from data.models import CartItem, Product
from data.schemas import OrderCreate
from data.catalog_product_utils import resolve_product_variant
from data.services_logistics_partner_pricing import quote_shipping_for_destination
from utils.config import settings



# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CartItemIn(BaseModel):
    product_id: int
    quantity: int
    selected_size: str = ""
    selected_color: str = ""


class CartSyncRequest(BaseModel):
    items: List[CartItemIn]


class CartShippingQuoteRequest(BaseModel):
    country: str
    city: str = ""
    subtotal: float = 0.0
    total_weight_kg: float = 0.0
    pickup_count: int | None = None
    dropoff_count: int | None = None
    items: List[CartItemIn] = []


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _normalize_variant(value: str | None) -> str:
    return (value or "").strip()


def _variant_key(product_id: int, selected_size: str | None, selected_color: str | None) -> tuple[int, str, str]:
    return product_id, _normalize_variant(selected_size), _normalize_variant(selected_color)


def _cart_row(item: CartItem) -> dict[str, Any]:
    snapshot: dict[str, Any] = _product_snapshot(item.product, cast(Any, item).selected_size, cast(Any, item).selected_color) if item.product else {"id": cast(Any, item).product_id}
    snapshot["quantity"] = cast(Any, item).quantity
    snapshot["cart_item_id"] = cast(Any, item).id
    snapshot["selected_size"] = cast(Any, item).selected_size or ""
    snapshot["selected_color"] = cast(Any, item).selected_color or ""
    return snapshot


def _load_cart_items(user_id: int, db: Session) -> list[CartItem]:
    return load_cart_items(db, user_id)


def _resolve_variant_or_raise(product: Product, selected_size: str | None, selected_color: str | None):
    variant = resolve_product_variant(product, selected_size, selected_color)
    has_variants = bool(getattr(product, "variants", []) or [])
    if has_variants and (_normalize_variant(selected_size) or _normalize_variant(selected_color)) and variant is None:
        raise HTTPException(status_code=422, detail="Selected variant is not available for '" + str(product.name) + "'")
    return variant


# ── Public API ────────────────────────────────────────────────────────────────

def get_cart(user_id: int, db: Session) -> List[dict]:
    items = _load_cart_items(user_id, db)
    # Filter out deleted/inactive products silently
    return [_cart_row(i) for i in items if i.product and not i.product.is_deleted]


def sync_cart(user_id: int, body: CartSyncRequest, db: Session) -> List[dict]:
    """
    Bulk-replace cart with the supplied items (called once on login to push
    the offline/localStorage cart to the server).

    Strategy: server items not in the incoming list are removed.  Incoming items
    replace server quantities (client wins on login sync).
    """
    if not body.items:
        # Empty sync — clear the server cart
        delete_cart_items_by_user(db, user_id)
        return []

    # Validate all product IDs exist and have stock
    product_ids = sorted({item.product_id for item in body.items})
    products = {
        p.id: p
        for p in get_products_by_ids(db, product_ids)
    }

    normalized_items: dict[tuple[int, str, str], CartItemIn] = {}
    for item in body.items:
        normalized_items[_variant_key(item.product_id, item.selected_size, item.selected_color)] = item

    incoming_keys = set(normalized_items.keys())
    existing_items = _load_cart_items(user_id, db)
    existing_by_key = {
        _variant_key(cast(Any, item).product_id, cast(Any, item).selected_size, cast(Any, item).selected_color): item
        for item in existing_items
    }

    actions: list[dict] = []

    for existing in existing_items:
        if _variant_key(cast(Any, existing).product_id, cast(Any, existing).selected_size, cast(Any, existing).selected_color) not in incoming_keys:
            actions.append({"op": "delete", "item": existing})

    for variant_key, item in normalized_items.items():
        if item.product_id not in products:
            continue  # skip unknown/deleted products
        qty = max(1, min(item.quantity, 999))
        _, selected_size, selected_color = variant_key
        variant = _resolve_variant_or_raise(products[item.product_id], selected_size, selected_color)
        available_stock = int(getattr(variant, "stock", cast(Any, products[item.product_id]).stock))
        if available_stock < qty:
            raise HTTPException(status_code=409, detail=f"Insufficient stock for '{products[item.product_id].name}'")
        existing = existing_by_key.get(variant_key)
        if existing:
            cast(Any, existing).quantity = qty
            actions.append({"op": "upsert", "item": existing})
        else:
            new_item = CartItem(
                user_id=user_id,
                product_id=item.product_id,
                quantity=qty,
                selected_size=selected_size,
                selected_color=selected_color,
            )
            actions.append({"op": "upsert", "item": new_item})

    sync_cart_items(db, user_id, actions)
    return get_cart(user_id, db)


def upsert_cart_item(user_id: int, product_id: int, quantity: int, selected_size: str | None, selected_color: str | None, db: Session) -> List[dict]:
    """Add or update a single item in the server cart."""
    if quantity <= 0:
        return remove_cart_item(user_id, product_id, selected_size, selected_color, db)

    product = get_active_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    qty = max(1, min(quantity, 999))
    normalized_size = _normalize_variant(selected_size)
    normalized_color = _normalize_variant(selected_color)
    variant = _resolve_variant_or_raise(product, normalized_size, normalized_color)
    available_stock = int(getattr(variant, "stock", cast(Any, product).stock))
    if available_stock < qty:
        raise HTTPException(status_code=409, detail=f"Insufficient stock for '{product.name}'")

    existing = get_cart_item_by_variant(
        db, user_id, product_id, normalized_size, normalized_color
    )
    upsert_cart_item(db, user_id, product_id, qty, normalized_size, normalized_color, existing)
    return get_cart(user_id, db)


def remove_cart_item(user_id: int, product_id: int, selected_size: str | None, selected_color: str | None, db: Session) -> List[dict]:
    delete_cart_item_by_variant(db, user_id, product_id, selected_size, selected_color)
    return get_cart(user_id, db)


def clear_cart(user_id: int, db: Session) -> dict:
    delete_cart_items_by_user(db, user_id)
    return {"detail": "Cart cleared"}


def get_cart_shipping_quote(body: CartShippingQuoteRequest, db: Session) -> dict[str, Any]:
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
        products, _ = _load_products_for_order(preview_order, db)
        supplier_totals = _group_supplier_totals(preview_order, products, db)
        if supplier_totals:
            shipping_amount, shipment_groups = _quote_supplier_groups(
                supplier_totals=supplier_totals,
                destination_country=country,
                destination_city=city,
                db=db,
            )
            partner_id, _, estimated_delivery_min, estimated_delivery_max = _resolve_order_level_logistics_fields(shipment_groups)
            partner_name = None
            if partner_id is not None:
                matching_quote = next((quote for quote in shipment_groups if quote.get("partner_id") == partner_id), None)
                partner_name = cast(str | None, matching_quote.get("partner_name")) if matching_quote else None
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

