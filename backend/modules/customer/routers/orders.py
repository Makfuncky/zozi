"""Customer orders router — consolidated from 3 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/customer/orders", tags=["customer", "orders"])


# === From cart.py ===
"""Cart router."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

import domains.customers.services.cart_service as cart_ctrl
from domains.catalog.services.products.products_service import resolve_product_variant
from infrastructure.database.database import get_db
from infrastructure.database.schemas import CartItemCreate
from domains.accounts.models.core import CartItem
from domains.governance.models.user import User
from domains.catalog.models.products import Product
from infrastructure.utils.dependencies import get_current_user


class CartItemUpdate(BaseModel):
    product_id: int | None = None
    quantity: int


def _serialize_cart_item(item: CartItem) -> dict:
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

@router.get("")
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.variants))
        .filter(CartItem.user_id == current_user.id)
        .all()
    )
    subtotal = sum((i.product.price * i.quantity) for i in items if i.product)
    normalized_items = [_serialize_cart_item(i) for i in items]
    return {"items": normalized_items, "subtotal": float(subtotal), "item_count": len(items)}
@router.post("/items")
def add_to_cart(payload: CartItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id, Product.is_active == True).first()
    if not product: raise HTTPException(404, "Product not found")
    selected_size = payload.selected_size or ""
    existing = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == payload.product_id,
        CartItem.selected_size == selected_size,
        CartItem.selected_color == payload.selected_color,
    ).first()
    if existing:
        existing.quantity += payload.quantity
    else:
        db.add(CartItem(
            user_id=current_user.id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            quantity=payload.quantity,
            selected_size=selected_size,
            selected_color=payload.selected_color,
        ))
    db.commit()
    return {"message": "Added to cart"}

@router.put("/sync")
def sync_cart(
    body: cart_ctrl.CartSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_ctrl.sync_cart(current_user.id, body, db)
@router.put("/items/{product_id}")
def update_cart_item(product_id: int, body: CartItemUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quantity = body.quantity
    item = db.query(CartItem).filter(CartItem.id == product_id, CartItem.user_id == current_user.id).first()
    if not item:
        item = db.query(CartItem).filter(CartItem.product_id == product_id, CartItem.user_id == current_user.id).first()
    if not item:
        product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
        if not product: raise HTTPException(404, "Product not found")
        if quantity > 0:
            item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
            db.add(item)
            db.commit()
        return {"message": "Updated"}
    if quantity <= 0:
        db.delete(item)
    else:
        item.quantity = quantity
    db.commit()
    return {"message": "Updated"}
@router.delete("/items/{product_id}")
def remove_from_cart(product_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == product_id, CartItem.user_id == current_user.id).first()
    if not item:
        item = db.query(CartItem).filter(CartItem.product_id == product_id, CartItem.user_id == current_user.id).first()
    if not item: raise HTTPException(404, "Item not found")
    db.delete(item); db.commit()
    return {"message": "Removed"}
@router.delete("")
def clear_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Cart cleared"}

@router.post("/shipping-quote")
def get_cart_shipping_quote(
    body: cart_ctrl.CartShippingQuoteRequest,
    db: Session = Depends(get_db),
):
    return cart_ctrl.get_cart_shipping_quote(body, db)


# === From customer_orders.py ===
"""AUTO-GENERATED — DO NOT EDIT MANUALLY (generated by routers/generated/auto_router.py)"""

from fastapi import APIRouter, Depends, Body, Query
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import get_current_user

from infrastructure.database.schemas import OrderCreate
from infrastructure.database.schemas import OrderPreviewOut
from domains.orders.services.core.order_admin import cancel_order
from domains.orders.services.core.order_admin import confirm_order_scan_receipt
from domains.orders.services.core.order_engine import create_order
from domains.orders.services.core.order_engine import get_order
from domains.orders.services.core.order_engine import get_order_invoice
from domains.orders.services.core.order_admin import get_order_tracking
from domains.orders.services.core.order_engine import get_orders
from domains.orders.services.core.order_engine import preview_order
from domains.orders.services.core.order_admin import respond_to_shipment_confirmation


@router.post("/orders", status_code=201, tags=['orders'])
def create_order_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    order: OrderCreate = Body(...)
):
    return create_order(current_user=current_user, db=db, order=order)

@router.post("/orders/preview", response_model=OrderPreviewOut, status_code=201, tags=['orders'])
def preview_order_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    order: OrderCreate = Body(...)
):
    return preview_order(current_user=current_user, db=db, order=order)

@router.get("/orders", status_code=200, tags=['orders'])
def get_orders_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0),
    limit: int = Query(50)
):
    return get_orders(current_user=current_user, db=db, skip=skip, limit=limit)

@router.get("/orders/{order_id}", status_code=200, tags=['orders'])
def get_order_route(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_order(order_id=order_id, current_user=current_user, db=db)

@router.get("/orders/{order_id}/invoice", status_code=200, tags=['orders'])
def get_order_invoice_route(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_order_invoice(order_id=order_id, current_user=current_user, db=db)

@router.get("/orders/{order_id}/tracking", status_code=200, tags=['orders'])
def get_order_tracking_route(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_order_tracking(order_id=order_id, current_user=current_user, db=db)

@router.post("/orders/{order_id}/scan-receipt", status_code=201, tags=['orders'])
def confirm_order_scan_receipt_route(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    data: dict = Body(...)
):
    return confirm_order_scan_receipt(order_id=order_id, current_user=current_user, db=db, data=data)

@router.post("/orders/{order_id}/cancel", status_code=201, tags=['orders'])
def cancel_order_route(
    order_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return cancel_order(order_id=order_id, current_user=current_user, db=db)

@router.post("/orders/{order_id}/confirmation-requests/{confirmation_id}/respond", status_code=201, tags=['orders'])
def respond_to_shipment_confirmation_route(
    order_id: int,
    confirmation_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    data: dict = Body(...)
):
    return respond_to_shipment_confirmation(order_id=order_id, confirmation_id=confirmation_id, current_user=current_user, db=db, data=data)


# === From returns.py ===
"""Returns router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from domains.orders.services.returns.service import bulk_update_return_requests
from domains.orders.services.returns.service import create_return_request
from domains.orders.services.returns.service import get_return_request
from domains.orders.ports import list_return_requests
from domains.orders.services.returns.service import update_return_request
from infrastructure.database.database import get_db
from infrastructure.database.schemas import ReturnRequestCreate, ReturnRequestOut, ReturnRequestUpdate
from domains.governance.models.user import User
from domains.orders.models.order_entities import ReturnRequest
from infrastructure.utils.dependencies import get_current_user, require_admin


class BulkReturnStatusUpdateBody(BaseModel):
    return_ids: list[int]
    status: str
    resolution_notes: Optional[str] = None
    notes: Optional[str] = None


def _user_context(user: User) -> dict:
    return {
        "id": getattr(user, "id", None),
        "username": getattr(user, "username", None),
        "role": getattr(user, "role", None),
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

@router.get("", response_model=list[ReturnRequestOut])
def list_returns(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    requests = list_return_requests(_user_context(current_user), db)
    return [_serialize_return(req) for req in requests]

@router.post("", response_model=ReturnRequestOut, status_code=201)
def create_return(payload: ReturnRequestCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = create_return_request(_user_context(current_user), payload, db)
    return _serialize_return(req)


@router.get("/{return_id}", response_model=ReturnRequestOut)
def get_return(return_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    req = get_return_request(return_id, _user_context(current_user), db)
    return _serialize_return(req)


@router.put("/bulk")
def bulk_update_returns(
    body: BulkReturnStatusUpdateBody,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
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
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    req = update_return_request(return_id, payload, _user_context(current_user), db)
    return _serialize_return(req)

@router.put("/{return_id}/status")
def update_return_status(return_id: int, status: str, notes: str = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    r = db.query(ReturnRequest).filter(ReturnRequest.id == return_id).first()
    if not r: raise HTTPException(404)
    r.status = status
    if notes: r.resolution_notes = notes
    db.commit()
    return {"message": "Updated"}


