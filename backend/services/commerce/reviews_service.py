"""Review read/write operations for the products domain.

This service is the single owner of direct DB access for review data.
Controllers/routers delegate all ``db.query(...)`` reads and
``session.add()/commit()`` writes here so the layer contract
(reads/writes via services) is honoured by the architecture audit.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import Product, Review


def get_review_by_id(db: Session, review_id: int) -> Review | None:
    """Fetch an active (non-deleted) review by id."""
    return (
        db.query(Review)
        .filter(Review.id == review_id, Review.is_deleted == False)  # noqa: E712
        .first()
    )


def list_product_reviews(db: Session, product_id: int) -> list[Review]:
    """Return the active reviews for ``product_id`` newest-first."""
    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .order_by(Review.created_at.desc())
        .all()
    )


def get_product(db: Session, product_id: int) -> Product | None:
    """Fetch a single product by id."""
    return db.query(Product).filter(Product.id == product_id).first()


def get_existing_review(db: Session, product_id: int, user_id: int) -> Review | None:
    """Return a prior (non-deleted) review by user for a product, if any."""
    return (
        db.query(Review)
        .filter(
            Review.product_id == product_id,
            Review.user_id == user_id,
            Review.is_deleted == False,  # noqa: E712
        )
        .first()
    )


def create_review(
    db: Session,
    product_id: int,
    user_id: int,
    rating: float,
    comment: str | None,
    image_url: str | None,
) -> Review:
    """Persist a new review and return the refreshed row."""
    review = Review(
        product_id=product_id,
        user_id=user_id,
        rating=rating,
        comment=comment,
        image_url=image_url,
        is_verified_purchase=False,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review_id: int) -> Review:
    """Soft-delete a review by id, returning the loaded row."""
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_deleted = True
    db.commit()
    return review



def list_review_ratings(db: Session, product_id: int) -> list:
    """Return all rating values for a product — delegated from controller."""
    return (
        db.query(Review.rating)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .all()
    )
