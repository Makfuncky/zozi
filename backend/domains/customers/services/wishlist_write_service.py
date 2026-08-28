"""Wishlist write service (SERVICES layer).

Owns all mutating database access for ``wishlist_items``. Routers and
controllers must not call ``db.add`` / ``db.delete`` / ``db.commit`` directly
for wishlist writes.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.catalog.ports import WishlistItem
import structlog

logger = structlog.get_logger(__name__)


def create_wishlist_item(db: Session, user_id: int, product_id: int) -> WishlistItem:
    item = WishlistItem(user_id=user_id, product_id=product_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def delete_wishlist_item(db: Session, item: WishlistItem) -> None:
    db.delete(item)
    db.commit()


def add_to_wishlist_safe(db: Session, user_id: int, product_id: int) -> dict:
    from domains.customers.services.wishlist_read_service import (
        product_exists as wishlist_product_exists,
        get_wishlist_item_by_product,
    )
    if not wishlist_product_exists(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    existing = get_wishlist_item_by_product(db, user_id, product_id)
    if existing:
        return {"product_id": product_id, "detail": "Already in wishlist"}
    item = create_wishlist_item(db, user_id, product_id)
    return {"product_id": item.product_id, "detail": "Added to wishlist"}


def remove_from_wishlist(db: Session, user_id: int, product_id: int) -> dict:
    from domains.customers.services.wishlist_read_service import get_wishlist_item_by_product
    item = get_wishlist_item_by_product(db, user_id, product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    delete_wishlist_item(db, item)
    return {"product_id": product_id, "detail": "Removed from wishlist"}


def clear_wishlist(db: Session, user_id: int) -> int:
    """Remove every wishlist item for a user. Returns the number deleted."""
    deleted = db.query(WishlistItem).filter(WishlistItem.user_id == user_id).delete()
    db.commit()
    return deleted
