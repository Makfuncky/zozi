"""Customer orders router — consolidated from 3 source files."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from decimal import Decimal

from infrastructure.security.dependencies import get_current_user, require_admin
from infrastructure.database.database import get_db
from infrastructure.database.schemas import CartItemCreate, CartSyncRequest, OrderCreate, OrderPreviewOut, ReturnRequestCreate, ReturnRequestOut, ReturnRequestUpdate
from infrastructure.utils.config import settings
from kernel.money import round_money, to_decimal
from domains.orders.ports import list_return_requests
from domains.orders.services.cart.service import (
    get_cart as svc_get_cart,
    add_to_cart as svc_add_to_cart,
    update_cart_item as svc_update_cart_item,
    remove_cart_item as svc_remove_cart_item,
    clear_cart as svc_clear_cart,
    get_cart_shipping_quote as svc_get_cart_shipping_quote,
    sync_cart as svc_sync_cart,
    CartShippingQuoteRequest,
)
from domains.orders.services.core.order_admin import cancel_order
from domains.orders.services.core.order_admin import confirm_order_scan_receipt
from domains.orders.services.core.order_admin import get_order_tracking
from domains.orders.services.core.order_admin import respond_to_shipment_confirmation
from domains.orders.services.core.order_engine import create_order
from domains.orders.services.core.order_engine import get_order
from domains.orders.services.core.order_engine import get_order_invoice
from domains.orders.services.core.order_engine import get_orders
from domains.orders.services.core.order_engine import preview_order
from domains.orders.services.returns.service import bulk_update_return_requests
from domains.orders.services.returns.service import create_return_request
from domains.orders.services.returns.service import get_return_request
from domains.orders.services.returns.service import update_return_request
from domains.customers.services.coupons_service import build_coupon_quote
from domains.promotions.services.engine.promotion_service import calculate_order_tier_discount
from domains.finance.services.ledger.general_ledger_service import calculate_tax
from rbac.dependencies import require_feature


router = APIRouter(prefix="/api/v1/customer/orders", tags=["customer", "orders"])


# === From cart.py ===
"""Cart router."""


class CartItemUpdate(BaseModel):
    product_id: int | None = None
    quantity: int


@router.get("")
def get_cart(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.cart.manage"))
):
    result = svc_get_cart(current_user.id, db)
    return {"items": result.items, "subtotal": result.subtotal, "item_count": result.item_count}


@router.post("/items")
def add_to_cart(payload: CartItemCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.cart.manage"))
):
    return svc_add_to_cart(current_user.id, payload, db)


@router.put("/sync")
def sync_cart(
    body: CartSyncRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.cart.manage")),
):
    return svc_sync_cart(current_user.id, body, db)


@router.put("/items/{product_id}")
def update_cart_item(product_id: int, body: CartItemUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.cart.manage"))
):
    return svc_update_cart_item(
        user_id=current_user.id,
        product_id=product_id,
        quantity=body.quantity,
        selected_size="",
        selected_color="",
        db=db,
    )


@router.delete("/items/{product_id}")
def remove_from_cart(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.cart.manage"))
):
    return svc_remove_cart_item(current_user.id, product_id, db)


@router.delete("")
def clear_cart(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.cart.manage"))
):
    return svc_clear_cart(current_user.id, db)


@router.post("/shipping-quote")
def get_cart_shipping_quote(
    body: CartShippingQuoteRequest,
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.delivery.estimates")),
):
    return svc_get_cart_shipping_quote(body, db)


# === Cart Totals — server-side pricing (Law 14: business logic in backend) ===


class CartTotalsItem(BaseModel):
    product_id: int
    price: float
    quantity: int


class CartTotalsRequest(BaseModel):
    items: list[CartTotalsItem]
    coupon_code: str | None = None
    country: str | None = None


@router.post("/totals")
def calculate_cart_totals(
    body: CartTotalsRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.cart.manage")),
):
    """Compute cart totals server-side. Frontend must NOT duplicate this logic."""
    subtotal = sum(item.price * item.quantity for item in body.items)

    # Coupon discount
    discount = Decimal("0")
    coupon_code = None
    if body.coupon_code and body.coupon_code.strip():
        try:
            coupon_quote = build_coupon_quote(body.coupon_code.strip(), Decimal(str(subtotal)), db)
            discount = round_money(Decimal(str(coupon_quote["discount_amount"])))
            coupon_code = coupon_quote["code"]
        except Exception:
            discount = Decimal("0")

    # Tier discount
    coupon_adjusted = Decimal(str(subtotal)) - discount
    try:
        tier_discount, _ = calculate_order_tier_discount(coupon_adjusted, db)
        discount = round_money(discount + tier_discount)
    except Exception:
        pass

    after_discount = max(Decimal("0"), Decimal(str(subtotal)) - discount)

    # Shipping (flat-rate with free threshold)
    free_threshold = Decimal(str(getattr(settings, "free_shipping_threshold", 0) or 0))
    flat_rate = Decimal(str(getattr(settings, "shipping_flat_rate", 0) or 0))
    shipping = Decimal("0") if (free_threshold > 0 and after_discount >= free_threshold) else flat_rate

    # Tax
    country_code = (body.country or current_user.get("preferred_country") or "OM").upper()
    tax_amount = Decimal("0")
    tax_type = "VAT"
    try:
        tax_result = calculate_tax(float(after_discount), country_code, db)
        tax_amount = round_money(Decimal(str(tax_result.get("tax_amount") or 0)))
        tax_type = str(tax_result.get("tax_type") or "VAT").upper()
    except Exception:
        vat_rate = Decimal(str(getattr(settings, "vat_rate", 0.05) or 0))
        tax_amount = round_money(after_discount * vat_rate)
        tax_type = "VAT"

    total = round_money(after_discount + shipping + tax_amount)

    return {
        "subtotal": float(round_money(Decimal(str(subtotal)))),
        "discount": float(discount),
        "coupon_code": coupon_code,
        "shipping": float(shipping),
        "tax_amount": float(tax_amount),
        "tax_type": tax_type,
        "total": float(total),
        "free_shipping_threshold": float(free_threshold),
        "free_shipping_applied": shipping == 0 and free_threshold > 0,
    }


# === From customer_orders.py ===
"""AUTO-GENERATED — DO NOT EDIT MANUALLY (generated by routers/generated/auto_router.py)"""


@router.post("/orders", status_code=201, tags=['orders'])
def create_order_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    order: OrderCreate = Body(...),
    _rf_gate: None = Depends(require_feature("orders.create")),
):
    return create_order(current_user=current_user, db=db, order=order)

@router.post("/orders/preview", response_model=OrderPreviewOut, status_code=201, tags=['orders'])
def preview_order_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    order: OrderCreate = Body(...),
    _rf_gate: None = Depends(require_feature("orders.create")),
):
    return preview_order(current_user=current_user, db=db, order=order)

@router.get("/orders", status_code=200, tags=['orders'])
def get_orders_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0),
    limit: int = Query(50),
    _rf_gate: None = Depends(require_feature("orders.list")),
):
    return get_orders(current_user=current_user, db=db, skip=skip, limit=limit)

@router.get("/orders/{order_id}", status_code=200, tags=['orders'])
def get_order_route(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.read")),
):
    return get_order(order_id=order_id, current_user=current_user, db=db)

@router.get("/orders/{order_id}/invoice", status_code=200, tags=['orders'])
def get_order_invoice_route(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.read")),
):
    return get_order_invoice(order_id=order_id, current_user=current_user, db=db)

@router.get("/orders/{order_id}/tracking", status_code=200, tags=['orders'])
def get_order_tracking_route(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("logistics.shipping.tracking")),
):
    return get_order_tracking(order_id=order_id, current_user=current_user, db=db)

@router.post("/orders/{order_id}/scan-receipt", status_code=201, tags=['orders'])
def confirm_order_scan_receipt_route(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    data: dict = Body(...),
    _rf_gate: None = Depends(require_feature("orders.update")),
):
    return confirm_order_scan_receipt(order_id=order_id, current_user=current_user, db=db, data=data)

@router.post("/orders/{order_id}/cancel", status_code=201, tags=['orders'])
def cancel_order_route(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.cancel")),
):
    return cancel_order(order_id=order_id, current_user=current_user, db=db)

@router.post("/orders/{order_id}/confirmation-requests/{confirmation_id}/respond", status_code=201, tags=['orders'])
def respond_to_shipment_confirmation_route(
    order_id: int,
    confirmation_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    data: dict = Body(...),
    _rf_gate: None = Depends(require_feature("orders.update")),
):
    return respond_to_shipment_confirmation(order_id=order_id, confirmation_id=confirmation_id, current_user=current_user, db=db, data=data)


# === From returns.py ===
"""Returns router."""


class BulkReturnStatusUpdateBody(BaseModel):
    return_ids: list[int]
    status: str
    resolution_notes: Optional[str] = None
    notes: Optional[str] = None


def _user_context(user) -> dict:
    return {
        "id": getattr(user, "id", None),
        "username": getattr(user, "username", None),
        "role": getattr(user, "role", None),
    }


def _serialize_return(req) -> dict:
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

@router.get("/returns", response_model=list[ReturnRequestOut])
def list_returns(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.returns.read"))
):
    requests = list_return_requests(_user_context(current_user), db)
    return [_serialize_return(req) for req in requests]


@router.post("/returns", response_model=ReturnRequestOut, status_code=201)
def create_return(payload: ReturnRequestCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.returns.request"))
):
    req = create_return_request(_user_context(current_user), payload, db)
    return _serialize_return(req)


@router.get("/{return_id}", response_model=ReturnRequestOut)
def get_return(return_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.returns.read"))
):
    req = get_return_request(return_id, _user_context(current_user), db)
    return _serialize_return(req)


@router.put("/bulk")
def bulk_update_returns(
    body: BulkReturnStatusUpdateBody,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.returns.manage")),
):
    payload = ReturnRequestUpdate(
        status=body.status,
        notes=body.resolution_notes if body.resolution_notes is not None else body.notes,
    )
    return bulk_update_return_requests(body.return_ids, payload, _user_context(current_user), db)


@router.put("/{return_id}", response_model=ReturnRequestOut)
def update_return(
    return_id: int,
    payload: ReturnRequestUpdate,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.returns.manage")),
):
    req = update_return_request(return_id, payload, _user_context(current_user), db)
    return _serialize_return(req)


@router.put("/{return_id}/status")
def update_return_status(return_id: int, status: str, notes: str = None,     _: dict = Depends(require_admin), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("orders.returns.manage"))
):
    payload = ReturnRequestUpdate(
        status=status,
        notes=notes,
    )
    req = update_return_request(return_id, payload, _user_context(_), db)
    return {"message": "Updated"}
