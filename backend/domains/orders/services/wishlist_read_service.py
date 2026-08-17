"""Wishlist read service (SERVICES layer).

Owns all read access for ``wishlist_items``. Routers and controllers must not
query the ORM directly for wishlist reads.

The live wishlist API is modelled on the ``WishlistItem`` table (schema
``customer``). Persistence and reads are delegated here so the controller
stays thin and the router stays free of any ``db.query``.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from models import Product, WishlistItem
from utils.pagination import SAFE_QUERY_LIMIT
import structlog
logger = structlog.get_logger(__name__)


def product_exists(db: Session, product_id: int) -> bool:
    return db.query(Product.id).filter(Product.id == product_id).first() is not None


def get_user_wishlist(
    db: Session,
    user_id: int,
    limit: int = SAFE_QUERY_LIMIT,
    cursor: Optional[int] = None,
) -> List[WishlistItem]:
    """Keyset (cursor) pagination over a user's wishlist, newest first.

    ``cursor`` is the ``id`` of the last item the caller saw; the next page
    returns items with a strictly smaller ``id`` under a stable ``id DESC``
    sort. This avoids position-based skip scans and the drift they cause when
    rows are inserted concurrently.
    """
    query = (
        db.query(WishlistItem)
        .options(selectinload(WishlistItem.product))
        .filter(WishlistItem.user_id == user_id)
    )
    if cursor is not None:
        query = query.filter(WishlistItem.id < int(cursor))
    return query.order_by(WishlistItem.id.desc()).limit(min(max(1, limit), SAFE_QUERY_LIMIT)).all()


def get_wishlist_item_by_product(
    db: Session, user_id: int, product_id: int
) -> Optional[WishlistItem]:
    return (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == user_id, WishlistItem.product_id == product_id)
        .first()
    )


def get_wishlist_item_by_id(
    db: Session, item_id: int, user_id: int
) -> Optional[WishlistItem]:
    return (
        db.query(WishlistItem)
        .filter(WishlistItem.id == item_id, WishlistItem.user_id == user_id)
        .first()
    )
