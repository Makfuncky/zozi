"""Wishlist router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import get_current_user
from domains.customers.services.wishlist_read_service import (
    get_user_wishlist,
    get_wishlist_item_by_product,
    product_exists,
)
from domains.customers.services.wishlist_write_service import (
    create_wishlist_item,
    delete_wishlist_item,
)

router = APIRouter(prefix="/api/v1/customer/wishlist")


@router.get("")
def get_wishlist(limit: int = 200, offset: int = 0, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_wishlist(db, current_user["id"], limit=limit)


@router.post("/{product_id}")
def add_to_wishlist(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if not product_exists(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    existing = get_wishlist_item_by_product(db, current_user["id"], product_id)
    if existing:
        return {"product_id": product_id, "detail": "Already in wishlist"}
    item = create_wishlist_item(db, current_user["id"], product_id)
    return {"product_id": item.product_id, "detail": "Added to wishlist"}


@router.delete("/{product_id}")
def remove_from_wishlist(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_wishlist_item_by_product(db, current_user["id"], product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    delete_wishlist_item(db, item)
    return {"product_id": product_id, "detail": "Removed from wishlist"}
