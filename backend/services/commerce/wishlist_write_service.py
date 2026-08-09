"""Wishlist write service (SERVICES layer).

Owns all mutating database access for ``wishlist_items``. Routers and
controllers must not call ``db.add`` / ``db.delete`` / ``db.commit`` directly
for wishlist writes.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from data.models import WishlistItem
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


def clear_wishlist(db: Session, user_id: int) -> int:
    """Remove every wishlist item for a user. Returns the number deleted."""
    deleted = db.query(WishlistItem).filter(WishlistItem.user_id == user_id).delete()
    db.commit()
    return deleted
