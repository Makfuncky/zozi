"""Wishlist controller (CONTROLLERS layer).

Coordinates wishlist business rules (product existence, ownership-scoped
lookup, duplicate prevention) and delegates ALL persistence to
``services.commerce.wishlist_read_service`` / ``wishlist_write_service``. It
must not issue ``db.query`` directly and must not perform commits.

The HTTP contract is declared with ``routers.generated.auto_router`` decorators
so the auto-router emits ``routers/public_commerce_wishlist.py``.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from sqlalchemy.orm import Session

from routers.generated.auto_router import delete, get, post

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


class WishlistItemOut(BaseModel):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


def _user_id(current_user) -> int:
    if isinstance(current_user, dict):
        return int(current_user["id"])
    return int(current_user.id)


@get("/api/v1", deps=["db", "user"], response_model=List[WishlistItemOut], tags=["wishlist"])
def get_wishlist(current_user, db: Session, limit: int = 200, cursor: Optional[int] = None) -> List[WishlistItemOut]:
    limit = max(1, min(200, limit))
    return service_get_user_wishlist(db, _user_id(current_user), limit=limit, cursor=cursor)


@post("/api/v1/{product_id}", deps=["db", "user"], response_model=WishlistItemOut, status_code=201, tags=["wishlist"])
def add_to_wishlist(product_id: int, current_user, db: Session):
    if not service_product_exists(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    existing = service_get_item_by_product(db, _user_id(current_user), product_id)
    if existing:
        return existing
    return service_create_item(db, _user_id(current_user), product_id)


@delete("/api/v1/{product_id}", deps=["db", "user"], response_model=dict, tags=["wishlist"])
def remove_from_wishlist(product_id: int, current_user, db: Session) -> dict:
    item = service_get_item_by_product(db, _user_id(current_user), product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    service_delete_item(db, item)
    return {"product_id": product_id, "detail": "Removed from wishlist"}


@delete("/api/v1", deps=["db", "user"], response_model=dict, tags=["wishlist"])
def clear_user_wishlist(current_user, db: Session) -> dict:
    removed = service_clear_wishlist(db, _user_id(current_user))
    return {"detail": "Wishlist cleared", "removed": removed}
