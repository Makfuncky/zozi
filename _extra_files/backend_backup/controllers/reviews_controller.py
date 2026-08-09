"""Reviews controller (CONTROLLERS layer).

Canonical coordinator for the product-reviews feature. Enforces reviews
business rules (authorization, validation, rating recompute) and delegates
ALL persistence to services.commerce.reviews_service. It must not import
models or issue db.query directly.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.commerce.reviews_service import (
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


def _to_user_map(current_user) -> dict:
    if isinstance(current_user, dict):
        return current_user
    return {
        "id": int(getattr(current_user, "id", 0)),
        "role": getattr(current_user, "role", None),
        "username": getattr(current_user, "username", None),
    }


def _parse_rating(payload: dict) -> int:
    try:
        rating = float(payload.get("rating"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="rating must be a number")
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")
    return int(rating)


def _serialize(review) -> dict:
    return {
        "id": review.id,
        "product_id": review.product_id,
        "user_id": review.user_id,
        "rating": review.rating,
        "title": review.title,
        "comment": review.comment,
        "image_url": review.image_url,
        "is_approved": review.is_approved,
        "is_verified_purchase": review.is_verified_purchase,
        "created_at": review.created_at,
        "country_code": review.country_code,
    }


def get_product_reviews(product_id: int, skip: int, limit: int, db: Session) -> List[dict]:
    rows = service_get_product_reviews(db, product_id, skip=skip, limit=limit)
    return [_serialize(r) for r in rows]


def get_review(review_id: int, db: Session) -> dict:
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return _serialize(review)


def create_review(product_id: int, payload: dict, current_user, db: Session) -> dict:
    user = _to_user_map(current_user)
    if not product_exists(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    if find_existing_review(db, product_id, user["id"]):
        raise HTTPException(status_code=409, detail="You have already reviewed this product")

    rating = _parse_rating(payload)
    purchased = has_verified_purchase(db, user["id"], product_id)

    review = service_create_review(
        db,
        product_id=product_id,
        user_id=user["id"],
        rating=rating,
        title=payload.get("title"),
        comment=payload.get("comment") or payload.get("body"),
        image_url=payload.get("image_url"),
        is_verified_purchase=purchased,
    )
    recompute_product_rating(db, product_id)
    return _serialize(review)


def update_review(review_id: int, payload: dict, current_user, db: Session) -> dict:
    user = _to_user_map(current_user)
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")
    rating = _parse_rating(payload)
    updates = {
        "rating": rating,
        "comment": payload.get("comment") or payload.get("body"),
        "image_url": payload.get("image_url"),
    }
    updated = service_update_review(db, review, updates)
    recompute_product_rating(db, updated.product_id)
    return _serialize(updated)


def delete_review(review_id: int, current_user, db: Session) -> dict:
    user = _to_user_map(current_user)
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != user["id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")
    service_soft_delete_review(db, review)
    return {"detail": "Review deleted"}
