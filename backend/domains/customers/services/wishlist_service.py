"""Wishlist service — delegates to wishlist_read_service and wishlist_write_service."""
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.catalog.models.products import Product, WishlistItem
from domains.customers.services.wishlist_read_service import (
    get_user_wishlist as _get_user_wishlist,
    get_wishlist_item_by_product,
)
from domains.customers.services.wishlist_write_service import (
    create_wishlist_item,
    delete_wishlist_item,
)
import structlog

logger = structlog.get_logger(__name__)


def get_user_wishlist(
    db: Session,
    user_id: int,
    limit: int = 100,
    cursor: Optional[int] = None,
) -> List[WishlistItem]:
    """Fetch the wishlist for a given user."""
    return _get_user_wishlist(db, user_id, limit=limit, cursor=cursor)


def add_to_wishlist(user_id: int, product_id: int, db: Session) -> dict:
    """Add a product to the user's wishlist."""
    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted.is_(False)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    existing = get_wishlist_item_by_product(db, user_id, product_id)
    if existing:
        return {"user_id": user_id, "product_id": product_id, "status": "already_exists"}
    item = create_wishlist_item(db, user_id, product_id)
    return {"user_id": user_id, "product_id": product_id, "status": "added", "item_id": item.id}


def remove_from_wishlist(user_id: int, product_id: int, db: Session) -> dict:
    """Remove a product from the user's wishlist."""
    item = get_wishlist_item_by_product(db, user_id, product_id)
    if not item:
        return {"user_id": user_id, "product_id": product_id, "status": "not_found"}
    delete_wishlist_item(db, item)
    return {"user_id": user_id, "product_id": product_id, "status": "removed"}
