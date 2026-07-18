"""
Reviews Controller — product review CRUD and rating aggregation logic.
"""
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Review, Product, Order, OrderItem
from db.schemas import ReviewCreate


def get_product_reviews(product_id: int, skip: int, limit: int, db: Session) -> List[Review]:
    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_review(product_id: int, review: ReviewCreate, current_user: dict, db: Session) -> Review:
    if not db.query(Product).filter(Product.id == product_id).first():
        raise HTTPException(status_code=404, detail="Product not found")

    existing = db.query(Review).filter(
        Review.product_id == product_id,
        Review.user_id == current_user["id"],
        Review.is_deleted == False,  # noqa: E712
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You have already reviewed this product")

    purchased = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == current_user["id"],
            OrderItem.product_id == product_id,
            Order.status.in_(["delivered", "completed"]),
        )
        .first()
    )

    db_review = Review(
        product_id=product_id,
        user_id=current_user["id"],
        rating=review.rating,
        comment=review.comment,
        image_url=review.image_url,
        is_verified_purchase=bool(purchased),
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)

    # Recalculate product average rating
    all_ratings = (
        db.query(Review.rating)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .all()
    )
    avg = sum(r[0] for r in all_ratings) / len(all_ratings)
    db.query(Product).filter(Product.id == product_id).update({"rating": round(avg, 2)})
    db.commit()
    return db_review


def update_review(review_id: int, review: ReviewCreate, current_user: dict, db: Session) -> Review:
    db_review = db.query(Review).filter(Review.id == review_id, Review.is_deleted == False).first()  # noqa: E712
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.user_id != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")
    setattr(db_review, "rating", review.rating)
    setattr(db_review, "comment", review.comment)
    setattr(db_review, "image_url", review.image_url)
    db.commit()
    db.refresh(db_review)
    return db_review


def delete_review(review_id: int, current_user: dict, db: Session) -> dict:
    db_review = db.query(Review).filter(Review.id == review_id, Review.is_deleted == False).first()  # noqa: E712
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.user_id != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")
    setattr(db_review, "is_deleted", True)
    db.commit()
    return {"detail": "Review deleted"}

