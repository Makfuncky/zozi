"""Cart router."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload
import controllers.cart_controller as cart_ctrl
from services.catalog.product_utils import resolve_product_variant
from data.db import get_db
from data.models import CartItem, Product, User
from data.schemas import CartItemCreate, CartOut, CartItemOut, ProductListOut
from utils.dependencies import get_current_user
from decimal import Decimal

from services.write_helpers import add_and_flush, commit_only, delete_only
router = APIRouter()

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
def get_cart(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(CartItem)
        .options(selectinload(CartItem.product).selectinload(Product.variants))
        .filter(CartItem.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
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
        add_and_flush(db, CartItem(
            user_id=current_user.id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            quantity=payload.quantity,
            selected_size=selected_size,
            selected_color=payload.selected_color,
        ))
    commit_only(db)
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
            add_and_flush(db, item)
            commit_only(db)
        return {"message": "Updated"}
    if quantity <= 0:
        delete_only(db, item)
    else:
        item.quantity = quantity
    commit_only(db)
    return {"message": "Updated"}
@router.delete("/items/{product_id}")
def remove_from_cart(product_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == product_id, CartItem.user_id == current_user.id).first()
    if not item:
        item = db.query(CartItem).filter(CartItem.product_id == product_id, CartItem.user_id == current_user.id).first()
    if not item: raise HTTPException(404, "Item not found")
    delete_only(db, item); commit_only(db)
    return {"message": "Removed"}
@router.delete("")
def clear_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    commit_only(db)
    return {"message": "Cart cleared"}

@router.post("/shipping-quote")
def get_cart_shipping_quote(
    body: cart_ctrl.CartShippingQuoteRequest,
    db: Session = Depends(get_db),
):
    return cart_ctrl.get_cart_shipping_quote(body, db)

