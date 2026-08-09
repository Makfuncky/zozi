"""Wishlist controller (CONTROLLERS layer).

Coordinates wishlist business rules (product existence, ownership-scoped
lookup, duplicate prevention) and delegates ALL persistence to
``services.commerce.wishlist_read_service`` / ``wishlist_write_service``. It
must not issue ``db.query`` directly and must not perform commits.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException

from sqlalchemy.orm import Session

from services.commerce.wishlist_read_service import (
    get_user_wishlist as service_get_user_wishlist,
    get_wishlist_item_by_id as service_get_item_by_id,
    get_wishlist_item_by_product as service_get_item_by_product,
    product_exists as service_product_exists,
)
from services.commerce.wishlist_write_service import (
    clear_wishlist as service_clear_wishlist,
    create_wishlist_item as service_create_item,
    delete_wishlist_item as service_delete_item,
)
import structlog
logger = structlog.get_logger(__name__)


def get_wishlist(
    user_id: int, db: Session, limit: int = 200, cursor: Optional[int] = None
) -> List:
    return service_get_user_wishlist(db, user_id, limit=limit, cursor=cursor)


def add_to_wishlist(product_id: int, user_id: int, db: Session):
    if not service_product_exists(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    existing = service_get_item_by_product(db, user_id, product_id)
    if existing:
        return existing
    return service_create_item(db, user_id, product_id)


def remove_from_wishlist(product_id: int, user_id: int, db: Session) -> dict:
    item = service_get_item_by_product(db, user_id, product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    service_delete_item(db, item)
    return {"product_id": product_id, "detail": "Removed from wishlist"}


def clear_user_wishlist(user_id: int, db: Session) -> dict:
    removed = service_clear_wishlist(db, user_id)
    return {"detail": "Wishlist cleared", "removed": removed}
