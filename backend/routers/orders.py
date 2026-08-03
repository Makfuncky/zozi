"""Orders routes restored around the recovered orders controller."""
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from data.dependencies_auth import get_current_user
from controllers.orders.orders_controller import (
    cancel_order as cancel_order_controller,
    confirm_order_scan_receipt as confirm_order_scan_receipt_controller,
    create_order as create_order_controller,
    get_order_invoice as get_order_invoice_controller,
    get_order as get_order_controller,
    get_order_tracking as get_order_tracking_controller,
    get_orders as get_orders_controller,
    preview_order as preview_order_controller,
    respond_to_shipment_confirmation as respond_to_shipment_confirmation_controller,
)
from data.db import get_db
from data.schemas import OrderCreate, OrderPreviewOut

router = APIRouter()


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


def _serialize_order_item(item) -> dict:
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


def _serialize_order(order) -> dict:
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


@router.get("")
def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return [_serialize_order(order) for order in get_orders_controller(current_user, db, skip=skip, limit=limit)]

@router.post("/preview", response_model=OrderPreviewOut)
def preview_order(payload: OrderCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return preview_order_controller(payload, current_user, db)


@router.get("/{order_id}")
def get_order(order_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return _serialize_order(get_order_controller(order_id, current_user, db))


@router.get("/{order_id}/tracking")
def get_order_tracking(order_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_order_tracking_controller(order_id, current_user, db)


@router.get("/{order_id}/invoice")
def get_order_invoice(order_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_order_invoice_controller(order_id, current_user, db)

@router.post("/{order_id}/scan-receipt")
def confirm_order_scan_receipt(order_id: int, payload: dict, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return confirm_order_scan_receipt_controller(order_id, payload, current_user, db)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return _serialize_order(create_order_controller(payload, current_user, db))

@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return _serialize_order(cancel_order_controller(order_id, current_user, db))

@router.post("/{order_id}/confirmation-requests/{confirmation_id}/respond")
def respond_to_shipment_confirmation(
    order_id: int,
    confirmation_id: int,
    payload: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return respond_to_shipment_confirmation_controller(order_id, confirmation_id, payload, current_user, db)

