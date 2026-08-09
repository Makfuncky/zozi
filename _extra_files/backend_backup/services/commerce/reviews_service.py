"""Reviews persistence service (SERVICES layer).

Owns all direct database access for product reviews. Routers and controllers
must not touch the ORM directly for reviews.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from models import Order, OrderItem, Product, Review


def get_product_reviews(
    db: Session, product_id: int, skip: int = 0, limit: int = 50
) -> List[Review]:
    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.is_deleted.is_(False))
        .order_by(Review.created_at.desc())
        .offset(max(0, skip))
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
    return db.query(Review).filter(Review.id == review_id, Review.is_deleted.is_(False)).first()


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
) -> Review:
    review = Review(
        product_id=product_id,
        user_id=user_id,
        rating=rating,
        title=title,
        comment=comment,
        image_url=image_url,
        is_verified_purchase=is_verified_purchase,
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
    for key, value in updates.items():
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
