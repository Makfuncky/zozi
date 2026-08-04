"""Service methods for wishlist read operations."""
from __future__ import annotations
from sqlalchemy.orm import Session
from data.models import WishlistItem


def get_user_wishlist(db: Session, user_id: int) -> list[WishlistItem]:
    """Get wishlist items for a user."""
    return (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == user_id)
        .order_by(WishlistItem.created_at.desc())
        .all()
    )


def get_wishlist_item_by_product(db: Session, user_id: int, product_id: int) -> WishlistItem | None:
    """Check if a product is in user's wishlist."""
    return (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == user_id, WishlistItem.product_id == product_id)
        .first()
    )


def get_wishlist_item_by_id(db: Session, item_id: int, user_id: int) -> WishlistItem | None:
    """Get a wishlist item by ID, scoped to user."""
    return (
        db.query(WishlistItem)
        .filter(WishlistItem.id == item_id, WishlistItem.user_id == user_id)
        .first()
    )


def add_to_wishlist(db: Session, user_id: int, product_id: int) -> WishlistItem:
    """Add a product to the user's wishlist."""
    item = WishlistItem(user_id=user_id, product_id=product_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_wishlist(db: Session, item_id: int, user_id: int) -> bool:
    """Remove an item from the wishlist."""
    item = get_wishlist_item_by_id(db, item_id, user_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True
