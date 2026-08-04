"""Cart router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

import controllers.cart_controller as cart_ctrl
from data.catalog_product_utils import resolve_product_variant
from services.orders.orders_router_service import (
    get_cart_items,
    add_cart_item,
    update_single_cart_item,
    remove_cart_item,
    clear_cart,
)
from data.db import get_db
from data.models import CartItem, Product, User
from data.schemas import CartItemCreate, CartOut, CartItemOut, ProductListOut
from utils.dependencies import get_current_user

router = APIRouter()

class CartItemUpdate(BaseModel):
    product_id: int | None = None
    quantity: int


@router.get("")
def get_cart_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_cart_items(db, current_user.id, skip=skip, limit=limit)


@router.post("/items")
def add_to_cart(
    payload: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_cart_item(
        db,
        current_user.id,
        payload.product_id,
        payload.quantity,
        payload.variant_id,
        payload.selected_size or "",
        payload.selected_color or "",
    )


@router.put("/sync")
def sync_cart(
    body: cart_ctrl.CartSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return cart_ctrl.sync_cart(current_user.id, body, db)


@router.put("/items/{product_id}")
def update_cart_item(
    product_id: int,
    body: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_single_cart_item(db, product_id, current_user.id, body.quantity)


@router.delete("/items/{product_id}")
def remove_from_cart(product_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return remove_cart_item(db, product_id, current_user.id)


@router.delete("")
def clear_cart_endpoint(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return clear_cart(db, current_user.id)


@router.post("/shipping-quote")
def get_cart_shipping_quote(
    body: cart_ctrl.CartShippingQuoteRequest,
    db: Session = Depends(get_db),
):
    return cart_ctrl.get_cart_shipping_quote(body, db)