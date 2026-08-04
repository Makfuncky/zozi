"""
Orders Router Service - Database operations for order-related routers.
All SQLAlchemy DB access is centralized here for the routers:
- cart
- returns
- logistics_orders_v2
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from data.models import CartItem, LogisticsPartner, Product, ReturnRequest, Shipment, User
from data.services_write_helpers import add_and_flush, commit_only


def serialize_cart_item(item: CartItem) -> dict:
    from data.catalog_product_utils import resolve_product_variant
    
    product = item.product
    selected_size = getattr(item, "selected_size", None) or ""
    selected_color = getattr(item, "selected_color", None) or ""
    variant_requested = bool(selected_size.strip() or selected_color.strip())
    variant = resolve_product_variant(product, selected_size, selected_color) if product else None

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
        "selected_color": selected_color,
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


def _as_float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _first_non_none(*values):
    for value in values:
        if value is not None:
            return value
    return None


def serialize_order_item(item) -> dict:
    return {
        "id": item.id,
        "product_id": item.product_id,
        "variant_id": getattr(item, "variant_id", None),
        "supplier_id": getattr(item, "supplier_id", None),
        "product_name": getattr(item, "product_name", None),
        "product_image": getattr(item, "product_image", None),
        "quantity": item.quantity,
        "unit_price": _as_float(_first_non_none(getattr(item, "unit_price", None), getattr(item, "price", None))),
        "total_price": _as_float(getattr(item, "total_price", None)),
        "price": _as_float(_first_non_none(getattr(item, "price", None), getattr(item, "unit_price", None))),
        "selected_size": getattr(item, "selected_size", None),
        "selected_color": getattr(item, "selected_color", None),
    }


def serialize_order(order) -> dict:
    items = [_serialize_order_item(item) for item in list(getattr(order, "items", []) or [])]
    return {
        "id": order.id,
        "order_number": getattr(order, "order_number", None),
        "customer_id": getattr(order, "customer_id", None),
        "user_id": getattr(order, "user_id", None),
        "status": getattr(order, "status", None),
        "status_label": getattr(order, "status_label", None),
        "payment_status": getattr(order, "payment_status", None),
        "payment_method": getattr(order, "payment_method", None),
        "payment_provider": getattr(order, "payment_provider", None),
        "payment_intent_id": getattr(order, "payment_intent_id", None),
        "shipping_address": getattr(order, "shipping_address", None),
        "billing_address": getattr(order, "billing_address", None),
        "subtotal": _as_float(getattr(order, "subtotal", None)),
        "shipping_fee": _as_float(getattr(order, "shipping_fee", None)),
        "tax_amount": _as_float(getattr(order, "tax_amount", None)),
        "discount_amount": _as_float(getattr(order, "discount_amount", None)),
        "total": _as_float(getattr(order, "total", None)),
        "currency": getattr(order, "currency", None),
        "coupon_code": getattr(order, "coupon_code", None),
        "notes": getattr(order, "notes", None),
        "admin_notes": getattr(order, "admin_notes", None),
        "created_at": getattr(order, "created_at", None),
        "updated_at": getattr(order, "updated_at", None),
        "confirmed_at": getattr(order, "confirmed_at", None),
        "shipped_at": getattr(order, "shipped_at", None),
        "delivered_at": getattr(order, "delivered_at", None),
        "cancelled_at": getattr(order, "cancelled_at", None),
        "paid_at": getattr(order, "paid_at", None),
        "tracking_number": getattr(order, "tracking_number", None),
        "subtotal_amount": _as_float(_first_non_none(getattr(order, "subtotal_amount", None), getattr(order, "subtotal", None))),
        "vat_amount": _as_float(_first_non_none(getattr(order, "vat_amount", None), getattr(order, "tax_amount", None))),
        "shipping_amount": _as_float(_first_non_none(getattr(order, "shipping_amount", None), getattr(order, "shipping_fee", None))),
        "total_amount": _as_float(_first_non_none(getattr(order, "total_amount", None), getattr(order, "total", None))),
        "customer_phone": getattr(order, "customer_phone", None),
        "delivery_location": getattr(order, "delivery_location", None),
        "delivery_note": getattr(order, "delivery_note", None),
        "payment_gateway_code": getattr(order, "payment_gateway_code", None),
        "payment_gateway_fee_amount": _as_float(getattr(order, "payment_gateway_fee_amount", None)),
        "payment_customer_total_amount": _as_float(getattr(order, "payment_customer_total_amount", None)),
        "payment_gateway_fee_passed_to_customer": getattr(order, "payment_gateway_fee_passed_to_customer", None),
        "items": items,
    }


def _serialize_return(req: ReturnRequest) -> dict:
    return {
        "id": getattr(req, "id", None),
        "order_id": getattr(req, "order_id", None),
        "order_item_id": getattr(req, "order_item_id", None),
        "customer_id": getattr(req, "user_id", None),
        "intent": getattr(req, "intent", "return"),
        "reason": getattr(req, "reason", None),
        "description": getattr(req, "description", None),
        "images": getattr(req, "images", None),
        "status": getattr(req, "status", None),
        "resolution": getattr(req, "resolution_notes", None),
        "resolution_notes": getattr(req, "resolution_notes", None),
        "refund_amount": getattr(req, "refund_amount", None),
        "items": getattr(req, "items", None),
        "return_window_days": getattr(req, "return_window_days", None),
        "delivered_at": getattr(req, "delivered_at", None),
        "return_deadline": getattr(req, "return_deadline", None),
        "created_at": getattr(req, "created_at", None),
        "updated_at": getattr(req, "updated_at", None),
    }


def _user_context(user: User) -> dict:
    return {
        "id": getattr(user, "id", None),
        "username": getattr(user, "username", None),
        "role": getattr(user, "role", None),
    }


# ── Cart Router Service Functions ───────────────────────────────────────────────

def get_cart_items(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    items = (
        db.query(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.variants))
        .filter(CartItem.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    subtotal = sum((i.product.price * i.quantity) for i in items if i.product)
    normalized_items = [serialize_cart_item(i) for i in items]
    return {"items": normalized_items, "subtotal": float(subtotal), "item_count": len(items)}


def get_cart_item_by_id(db: Session, item_id: int, user_id: int) -> Optional[CartItem]:
    return db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()


def get_cart_item_by_product(
    db: Session,
    product_id: int,
    user_id: int,
    selected_size: str,
    selected_color: str,
) -> Optional[CartItem]:
    return db.query(CartItem).filter(
        CartItem.user_id == user_id,
        CartItem.product_id == product_id,
        CartItem.selected_size == selected_size,
        CartItem.selected_color == selected_color,
    ).first()


def get_active_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()


def add_cart_item(
    db: Session,
    user_id: int,
    product_id: int,
    quantity: int,
    variant_id: Optional[int],
    selected_size: str,
    selected_color: str,
) -> dict:
    product = get_active_product(db, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    
    selected_size = selected_size or ""
    existing = get_cart_item_by_product(db, product_id, user_id, selected_size, selected_color)
    
    if existing:
        existing.quantity += quantity
    else:
        add_and_flush(db, CartItem(
            user_id=user_id,
            product_id=product_id,
            variant_id=variant_id,
            quantity=quantity,
            selected_size=selected_size,
            selected_color=selected_color,
        ))
    commit_only(db)
    return {"message": "Added to cart"}


def update_single_cart_item(
    db: Session,
    product_id: int,
    user_id: int,
    quantity: int,
) -> dict:
    item = get_cart_item_by_id(db, product_id, user_id)
    if not item:
        item = get_cart_item_by_product(db, product_id, user_id, "", "")
    if not item:
        product = get_active_product(db, product_id)
        if not product:
            raise HTTPException(404, "Product not found")
        if quantity > 0:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            add_and_flush(db, item)
            commit_only(db)
        return {"message": "Updated"}
    if quantity <= 0:
        from data.services_write_helpers import delete_only
        delete_only(db, item)
        commit_only(db)
    else:
        item.quantity = quantity
        commit_only(db)
    return {"message": "Updated"}


def remove_cart_item(
    db: Session,
    product_id: int,
    user_id: int,
) -> dict:
    item = get_cart_item_by_id(db, product_id, user_id)
    if not item:
        item = get_cart_item_by_product(db, product_id, user_id, "", "")
    if not item:
        raise HTTPException(404, "Item not found")
    from data.services_write_helpers import delete_only, commit_only
    delete_only(db, item)
    commit_only(db)
    return {"message": "Removed"}


def clear_cart(db: Session, user_id: int) -> dict:
    db.query(CartItem).filter(CartItem.user_id == user_id).delete()
    commit_only(db)
    return {"message": "Cart cleared"}


# ── Returns Router Service Functions ──────────────────────────────────────────

def serialize_return_request(req: ReturnRequest) -> dict:
    return {
        "id": getattr(req, "id", None),
        "order_id": getattr(req, "order_id", None),
        "order_item_id": getattr(req, "order_item_id", None),
        "customer_id": getattr(req, "user_id", None),
        "intent": getattr(req, "intent", "return"),
        "reason": getattr(req, "reason", None),
        "description": getattr(req, "description", None),
        "images": getattr(req, "images", None),
        "status": getattr(req, "status", None),
        "resolution": getattr(req, "resolution_notes", None),
        "resolution_notes": getattr(req, "resolution_notes", None),
        "refund_amount": getattr(req, "refund_amount", None),
        "items": getattr(req, "items", None),
        "return_window_days": getattr(req, "return_window_days", None),
        "delivered_at": getattr(req, "delivered_at", None),
        "return_deadline": getattr(req, "return_deadline", None),
        "created_at": getattr(req, "created_at", None),
        "updated_at": getattr(req, "updated_at", None),
    }


def get_return_by_id(db: Session, return_id: int) -> Optional[ReturnRequest]:
    return db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()


def update_return_status(db: Session, return_id: int, status: str, notes: Optional[str] = None) -> dict:
    r = get_return_by_id(db, return_id)
    if not r:
        raise HTTPException(404)
    r.status = status
    if notes:
        r.resolution_notes = notes
    from data.services_write_helpers import commit_only
    commit_only(db)
    return {"message": "Updated"}


# ── Logistics Orders Router Service Functions ──────────────────────────────────

def get_logistics_partner_by_user(db: Session, user_id: int) -> Optional[LogisticsPartner]:
    return db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user_id).first()


def get_shipments_for_partner(
    db: Session,
    partner_id: int,
    skip: int,
    limit: int,
) -> list[dict]:
    shipments = (
        db.query(Shipment)
        .filter(Shipment.assigned_partner_id == partner_id)
        .order_by(Shipment.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": s.id,
            "order_id": s.order_id,
            "status": s.status,
            "tracking_number": s.tracking_number,
            "scan_code": s.scan_code,
            "current_hub": s.current_hub,
            "package_weight_kg": float(s.package_weight_kg) if s.package_weight_kg else None,
            "packaged_at": s.packaged_at.isoformat() if s.packaged_at else None,
            "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
            "estimated_delivery": s.estimated_delivery.isoformat() if s.estimated_delivery else None,
            "actual_delivery": s.actual_delivery.isoformat() if s.actual_delivery else None,
            "delivery_signature_name": s.delivery_signature_name,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in shipments
    ]


def get_order_shipment_label(db: Session, order_id: int) -> Optional[dict]:
    from .order_tracking_service import get_order_shipment_label as label_service
    return label_service(order_id, db)
def get_order_by_id(db: Session, record_id: int) -> Optional[Order]:
    return db.query(Order).filter(Order.id == record_id).first()


def get_order_first(db: Session, **filters) -> Optional[Order]:
    query = db.query(Order)
    for key, value in filters.items():
        query = query.filter(getattr(Order, key) == value)
    return query.limit(1).first()


def list_unknown(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.offset(skip).limit(limit).all()


def get_shipment_first(db: Session, **filters) -> Optional[Shipment]:
    query = db.query(Shipment)
    for key, value in filters.items():
        query = query.filter(getattr(Shipment, key) == value)
    return query.limit(1).first()


def get_shipmentevent_first(db: Session, **filters) -> Optional[ShipmentEvent]:
    query = db.query(ShipmentEvent)
    for key, value in filters.items():
        query = query.filter(getattr(ShipmentEvent, key) == value)
    return query.limit(1).first()


def get_suppliernotificationpreference_first(db: Session, **filters) -> Optional[SupplierNotificationPreference]:
    query = db.query(SupplierNotificationPreference)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierNotificationPreference, key) == value)
    return query.limit(1).first()


def get_supplierdispute_first(db: Session, **filters) -> Optional[SupplierDispute]:
    query = db.query(SupplierDispute)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierDispute, key) == value)
    return query.limit(1).first()


def get_supplierdispute_by_id(db: Session, record_id: int) -> Optional[SupplierDispute]:
    return db.query(SupplierDispute).filter(SupplierDispute.id == record_id).first()


def list_supplierdispute(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[SupplierDispute]:
    query = db.query(SupplierDispute)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierDispute, key) == value)
    return query.offset(skip).limit(limit).all()


def get_user_by_id(db: Session, record_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == record_id).first()


def get_product_first(db: Session, **filters) -> Optional[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.limit(1).first()


def list_supplierprofile(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[SupplierProfile]:
    query = db.query(SupplierProfile)
    for key, value in filters.items():
        query = query.filter(getattr(SupplierProfile, key) == value)
    return query.offset(skip).limit(limit).all()


def get_shippingzone_first(db: Session, **filters) -> Optional[ShippingZone]:
    query = db.query(ShippingZone)
    for key, value in filters.items():
        query = query.filter(getattr(ShippingZone, key) == value)
    return query.limit(1).first()


def get_logisticspartner_by_id(db: Session, record_id: int) -> Optional[LogisticsPartner]:
    return db.query(LogisticsPartner).filter(LogisticsPartner.id == record_id).first()


def list_shipment(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Shipment]:
    query = db.query(Shipment)
    for key, value in filters.items():
        query = query.filter(getattr(Shipment, key) == value)
    return query.offset(skip).limit(limit).all()


def list_user(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.offset(skip).limit(limit).all()


def get_shipmentconfirmation_first(db: Session, **filters) -> Optional[ShipmentConfirmation]:
    query = db.query(ShipmentConfirmation)
    for key, value in filters.items():
        query = query.filter(getattr(ShipmentConfirmation, key) == value)
    return query.limit(1).first()


def get_returnrequest_first(db: Session, **filters) -> Optional[ReturnRequest]:
    query = db.query(ReturnRequest)
    for key, value in filters.items():
        query = query.filter(getattr(ReturnRequest, key) == value)
    return query.limit(1).first()


def get_shipment_by_id(db: Session, record_id: int) -> Optional[Shipment]:
    return db.query(Shipment).filter(Shipment.id == record_id).first()


def list_orderitem(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[OrderItem]:
    query = db.query(OrderItem)
    for key, value in filters.items():
        query = query.filter(getattr(OrderItem, key) == value)
    return query.offset(skip).limit(limit).all()


def list_product(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.offset(skip).limit(limit).all()


def get_unknown_scalar(db: Session, column: str, **filters) -> Any:
    query = db.query(getattr(Unknown, column))
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.scalar()


def get_orderitem_first(db: Session, **filters) -> Optional[OrderItem]:
    query = db.query(OrderItem)
    for key, value in filters.items():
        query = query.filter(getattr(OrderItem, key) == value)
    return query.limit(1).first()


def get_returnrequest_by_id(db: Session, record_id: int) -> Optional[ReturnRequest]:
    return db.query(ReturnRequest).filter(ReturnRequest.id == record_id).first()

def _db_order_query_0(db: Session) -> Optional[Any]:
    result = db.query(Order).options(selectinload(Order.items).selectinload(OrderItem.product))
    return result
    """Read-only query delegated from controller."""

def _db_shipment_query_1(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_shipmentevent_query_2(db: Session) -> Optional[Any]:
    return db.query(ShipmentEvent)
    """Read-only query delegated from controller."""

def _db_suppliernotificationpreference_query_0(db: Session) -> Optional[Any]:
    return db.query(SupplierNotificationPreference)
    """Read-only query delegated from controller."""

def _db_supplierdispute_query_1(db: Session, supplier_id: Any) -> Optional[Any]:
    result = db.query(SupplierDispute).filter(SupplierDispute.supplier_id == supplier_id)
    return result
    """Read-only query delegated from controller."""

def _db_supplierdispute_query_2(db: Session) -> Optional[Any]:
    return db.query(SupplierDispute)
    """Read-only query delegated from controller."""

def _db_supplierdispute_query_3(db: Session) -> Optional[Any]:
    result = db.query(SupplierDispute)
    return result
    """Read-only query delegated from controller."""

def _db_supplierdispute_all_4(db: Session, id: Any, ids: Any, in_: Any) -> Optional[Any]:
    result = db.query(SupplierDispute).filter(SupplierDispute.id.in_(ids)).all()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_query_0(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_shipmentevent_query_1(db: Session) -> Optional[Any]:
    return db.query(ShipmentEvent)
    """Read-only query delegated from controller."""

def _db_user_first_2(db: Session, current_user: Any, id: Any) -> Optional[Any]:
    result = db.query(User).filter(User.id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_product_all_3(db: Session, False: Any, id: Any, in_: Any, keys: Any, requested_quantities: Any) -> list[Any]:
    return for product in db.query(Product).options(selectinload(Product.variants)).filter( Product.id.in_(requested_quantities.keys()), Product.is_deleted == False,  # noqa: E712 ).with_for_update().all()
    """Read-only query delegated from controller."""

def _db_supplierprofile_all_4(db: Session, in_: Any, keys: Any, supplier_totals: Any, user_id: Any) -> list[Any]:
    return for profile in db.query(SupplierProfile).filter(SupplierProfile.user_id.in_(supplier_totals.keys())).all()
    """Read-only query delegated from controller."""

def _db_shippingzone_query_5(db: Session) -> Optional[Any]:
    return db.query(ShippingZone)
    """Read-only query delegated from controller."""

def _db_order_query_6(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_order_query_7(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_logisticspartner_first_8(db: Session, user_id: Any) -> Optional[Any]:
    result = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == user_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_order_query_9(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_shipment_all_10(db: Session, order_id: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.order_id == order_id).order_by(Shipment.created_at.asc()).all()
    return result
    """Read-only query delegated from controller."""

def _db_shipmentevent_query_11(db: Session) -> Optional[Any]:
    return db.query(ShipmentEvent)
    """Read-only query delegated from controller."""

def _db_user_all_12(db: Session, id: Any, in_: Any, supplier_ids: Any) -> list[Any]:
    return db.query(User).filter(User.id.in_(supplier_ids)).all()
    """Read-only query delegated from controller."""

def _db_shipment_query_13(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_shipment_all_14(db: Session, order_id: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.order_id == order_id).order_by(Shipment.created_at.asc()).all()
    return result
    """Read-only query delegated from controller."""

def _db_shipmentevent_query_15(db: Session) -> Optional[Any]:
    return db.query(ShipmentEvent)
    """Read-only query delegated from controller."""

def _db_shipmentconfirmation_query_16(db: Session) -> Optional[Any]:
    return db.query(ShipmentConfirmation)
    """Read-only query delegated from controller."""

def _db_returnrequest_query_17(db: Session) -> Optional[Any]:
    return db.query(ReturnRequest)
    """Read-only query delegated from controller."""

def _db_shipmentconfirmation_first_18(db: Session, confirmation_id: Any, id: Any, order_id: Any) -> Optional[Any]:
    result = db.query(ShipmentConfirmation).filter( ShipmentConfirmation.id == confirmation_id, ShipmentConfirmation.order_id == order_id, ).first()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_first_19(db: Session, confirmation: Any, id: Any, shipment_id: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.id == confirmation.shipment_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_order_first_20(db: Session, id: Any, order_id: Any, shipment: Any) -> Optional[Any]:
    result = db.query(Order).filter(Order.id == shipment.order_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_all_21(db: Session, id: Any, order: Any, order_id: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.order_id == order.id).all()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_all_22(db: Session, order_id: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.order_id == order_id).all()
    return result
    """Read-only query delegated from controller."""

def _db_shipment_all_23(db: Session, order_id: Any) -> Optional[Any]:
    result = db.query(Shipment).filter(Shipment.order_id == order_id).all()
    return result
    """Read-only query delegated from controller."""

def _db_order_first_24(db: Session, current_user: Any, id: Any, order_id: Any, user_id: Any) -> Optional[Any]:
    result = db.query(Order).filter( Order.id == order_id, Order.user_id == current_user["id"], ).first()
    return result
    """Read-only query delegated from controller."""

def _db_orderitem_all_0(db: Session, id: Any, order: Any, order_id: Any) -> list[Any]:
    return return db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    """Read-only query delegated from controller."""

def _db_product_all_1(db: Session, id: Any, in_: Any, product_ids: Any) -> list[Any]:
    return {cast(int, p.id): p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()}
    """Read-only query delegated from controller."""

def _db_shipment_query_2(db: Session) -> Optional[Any]:
    return db.query(Shipment)
    """Read-only query delegated from controller."""

def _db_order_query_3(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_order_query_4(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_order_first_5(db: Session, current_user: Any, id: Any, order_id: Any, payload: Any, user_id: Any) -> Optional[Any]:
    result = db.query(Order).filter(Order.id == payload.order_id, Order.user_id == current_user["id"]).first()
    return result
    """Read-only query delegated from controller."""

def _db_orderitem_query_6(db: Session) -> Optional[Any]:
    return db.query(OrderItem)
    """Read-only query delegated from controller."""

def _db_returnrequest_query_7(db: Session, order_id: Any, payload: Any) -> Optional[Any]:
    result = db.query(ReturnRequest).filter(ReturnRequest.order_id == payload.order_id)
    return result
    """Read-only query delegated from controller."""

def _db_returnrequest_query_8(db: Session) -> Optional[Any]:
    result = db.query(ReturnRequest).options( selectinload(ReturnRequest.order).selectinload(Order.items).selectinload(OrderItem.product) )
    return result
    """Read-only query delegated from controller."""

def _db_returnrequest_query_9(db: Session) -> Optional[Any]:
    return db.query(ReturnRequest)
    """Read-only query delegated from controller."""

def _db_order_first_10(db: Session, id: Any, order_id: Any, req: Any) -> Optional[Any]:
    result = db.query(Order).filter(Order.id == req.order_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_order_first_11(db: Session, id: Any, order_id: Any, req: Any) -> Optional[Any]:
    result = db.query(Order).filter(Order.id == req.order_id).first()
    return result
    """Read-only query delegated from controller."""

def _db_returnrequest_query_12(db: Session) -> Optional[Any]:
    return db.query(ReturnRequest)
    """Read-only query delegated from controller."""

def _db_product_first_13(db: Session, id: Any, item: Any, product_id: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.id == item["product_id"], Product.supplier_id == supplier_id, ).first()
    return result
    """Read-only query delegated from controller."""


def count_username_map(db: Session, user_ids: list[int]) -> dict[int, str]:
    """Look up usernames for a list of user IDs � delegated from controller."""
    user_rows = db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
    return {r.id: r.username for r in user_rows}
