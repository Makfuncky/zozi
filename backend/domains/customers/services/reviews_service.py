"""Reviews persistence service (SERVICES layer).

Owns all direct database access for product reviews. Routers and controllers
must not touch the ORM directly for reviews.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from domains.catalog.models.products import Product, Review
from domains.orders.models.orders import Order, OrderItem
import structlog

logger = structlog.get_logger(__name__)


def get_product_reviews(
    db: Session, product_id: int, limit: int = 50, cursor: Optional[int] = None
) -> List[Review]:
    """Keyset (cursor) pagination over a product's reviews.

    ``cursor`` is the ``id`` of the last review seen by the caller; the next
    page returns reviews with a strictly smaller ``id`` (combined with a stable
    ``(created_at DESC, id DESC)`` sort), which avoids position-based skip
    scans and drift when rows are inserted concurrently.
    """
    query = (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.product_id == product_id, Review.is_deleted.is_(False))
    )
    if cursor is not None:
        query = query.filter(Review.id < int(cursor))
    return (
        query.order_by(Review.created_at.desc(), Review.id.desc())
        .limit(min(max(1, limit), 200))
        .all()
    )


def product_exists(db: Session, product_id: int) -> bool:
    return db.query(Product.id).filter(Product.id == product_id).first() is not None


def find_existing_review(db: Session, product_id: int, user_id: int) -> Optional[Review]:
    return (
        db.query(Review)
        .filter(
            Review.product_id == product_id,
            Review.user_id == user_id,
            Review.is_deleted.is_(False),
        )
        .first()
    )


def get_review_by_id(db: Session, review_id: int) -> Optional[Review]:
    return (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.id == review_id, Review.is_deleted.is_(False))
        .first()
    )


def has_verified_purchase(db: Session, user_id: int, product_id: int) -> bool:
    return (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            OrderItem.product_id == product_id,
            Order.status.in_(["delivered", "completed"]),
        )
        .first()
        is not None
    )


def create_review(
    db: Session,
    *,
    product_id: int,
    user_id: int,
    rating: int,
    title: Optional[str] = None,
    comment: Optional[str] = None,
    image_url: Optional[str] = None,
    is_verified_purchase: bool = False,
    country_code: Optional[str] = None,
) -> Review:
    if not 1 <= int(rating) <= 5:
        raise HTTPException(status_code=422, detail="rating must be between 1 and 5")
    review = Review(
        product_id=product_id,
        user_id=user_id,
        rating=int(rating),
        title=title,
        comment=comment,
        image_url=image_url,
        is_verified_purchase=is_verified_purchase,
        country_code=country_code,
        created_by=user_id,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def soft_delete_review(db: Session, review: Review) -> None:
    review.is_deleted = True
    db.add(review)
    db.commit()


def update_review(db: Session, review: Review, updates: dict) -> Review:
    allowed_fields = {"rating", "title", "comment", "image_url", "is_verified_purchase"}
    for key, value in updates.items():
        if key not in allowed_fields:
            continue
        setattr(review, key, value)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def recompute_product_rating(db: Session, product_id: int) -> None:
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        return
    ratings = (
        db.query(Review.rating)
        .filter(Review.product_id == product_id, Review.is_deleted.is_(False))
        .all()
    )
    product.rating = round(sum(r[0] for r in ratings) / len(ratings), 2) if ratings else 0
    db.add(product)
    db.commit()
