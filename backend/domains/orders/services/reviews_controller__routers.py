"""Reviews controller (CONTROLLERS layer).

Canonical coordinator for the product-reviews feature. Enforces reviews
business rules (authorization, duplicate prevention, verified-purchase
detection, rating recompute) and delegates ALL persistence to
services.commerce.reviews_service. It must not issue db.query directly.

The HTTP contract is declared with ``routers.generated.auto_router`` decorators
so the auto-router emits ``routers/public_commerce_reviews.py``.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException

from infrastructure.database.schemas import ReviewCreate, ReviewOut
from sqlalchemy.orm import Session

from routers.generated.auto_router import delete, get, post, put

from domains.orders.services.reviews_service import (
    create_review as service_create_review,
    find_existing_review,
    get_product_reviews as service_get_product_reviews,
    get_review_by_id,
    has_verified_purchase,
    product_exists,
    recompute_product_rating,
    soft_delete_review as service_soft_delete_review,
    update_review as service_update_review,
)
import structlog
logger = structlog.get_logger(__name__)


def _to_user_map(current_user) -> dict:
    if isinstance(current_user, dict):
        return current_user
    return {
        "id": int(getattr(current_user, "id", 0)),
        "role": getattr(current_user, "role", None),
        "username": getattr(current_user, "username", None),
        "country_code": getattr(current_user, "country_code", None),
    }


def _serialize(review, username: Optional[str] = None) -> dict:
    owner_name = username
    if owner_name is None and getattr(review, "user", None) is not None:
        owner_name = getattr(review.user, "username", None)
    return {
        "id": review.id,
        "product_id": review.product_id,
        "user_id": review.user_id,
        "username": owner_name,
        "rating": review.rating,
        "title": review.title,
        "comment": review.comment,
        "image_url": review.image_url,
        "is_approved": review.is_approved,
        "is_verified_purchase": review.is_verified_purchase,
        "created_at": review.created_at,
        "country_code": review.country_code,
    }


@get("/api/v1/reviews/products/{product_id}", deps=["db"], query=["limit", "cursor"], response_model=List[ReviewOut], tags=["reviews"])
def get_product_reviews(
    product_id: int, db: Session, limit: int = 50, cursor: Optional[int] = None
) -> List[dict]:
    limit = max(1, min(200, limit))
    rows = service_get_product_reviews(db, product_id, limit=limit, cursor=cursor)
    return [
        _serialize(r, username=r.user.username if getattr(r, "user", None) else None)
        for r in rows
    ]


@get("/api/v1/reviews", deps=["db"], query=["product_id", "limit", "cursor"], response_model=List[ReviewOut], tags=["reviews"])
def list_reviews(
    db: Session, product_id: Optional[int] = None, limit: int = 50, cursor: Optional[int] = None
) -> List[dict]:
    """Mirrors the legacy router's GET /api/v1/reviews (list reviews for a product supplied
    as a query parameter). The auto-router renders query params as ``Query(None)``,
    so the original ``required`` contract is preserved by rejecting a missing
    ``product_id`` here."""
    if product_id is None:
        raise HTTPException(status_code=400, detail="product_id query parameter is required")
    limit = max(1, min(200, limit))
    return get_product_reviews(product_id, db=db, limit=limit, cursor=cursor)


@get("/api/v1/reviews/{review_id}", deps=["db"], response_model=ReviewOut, tags=["reviews"])
def get_review(review_id: int, db: Session) -> dict:
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return _serialize(review)


@post("/api/v1/reviews/products/{product_id}", deps=["db", "user"], body=ReviewCreate, response_model=ReviewOut, status_code=201, tags=["reviews"])
def create_review(product_id: int, review: ReviewCreate, current_user, db: Session) -> dict:
    user = _to_user_map(current_user)
    if not product_exists(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    if find_existing_review(db, product_id, user["id"]):
        raise HTTPException(status_code=409, detail="You have already reviewed this product")

    purchased = has_verified_purchase(db, user["id"], product_id)

    new_review = service_create_review(
        db,
        product_id=product_id,
        user_id=user["id"],
        rating=int(review.rating),
        title=review.title,
        comment=review.comment,
        image_url=review.image_url,
        is_verified_purchase=purchased,
        country_code=user.get("country_code"),
    )
    recompute_product_rating(db, product_id)
    return _serialize(new_review, username=user.get("username"))


@put("/api/v1/reviews/{review_id}", deps=["db", "user"], body=ReviewCreate, response_model=ReviewOut, tags=["reviews"])
def update_review(review_id: int, review: ReviewCreate, current_user, db: Session) -> dict:
    user = _to_user_map(current_user)
    existing = get_review_by_id(db, review_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Review not found")
    if existing.user_id != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")

    updates = {
        "rating": int(review.rating),
        "comment": review.comment,
        "image_url": review.image_url,
        "updated_by": user["id"],
    }
    updated = service_update_review(db, existing, updates)
    recompute_product_rating(db, updated.product_id)
    return _serialize(updated, username=user.get("username"))


@delete("/api/v1/reviews/{review_id}", deps=["db", "user"], response_model=ReviewOut, tags=["reviews"])
def delete_review(review_id: int, current_user, db: Session) -> dict:
    user = _to_user_map(current_user)
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")
    service_soft_delete_review(db, review)
    return _serialize(review, username=user.get("username"))

