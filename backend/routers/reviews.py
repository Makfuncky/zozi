"""Reviews router."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from data.db import get_db
from data.schemas import ReviewCreate
from data.models import User
from utils.dependencies import get_current_user
from services.reviews_service import (
    create_review,
    delete_review,
    get_existing_review,
    get_product,
    get_review_by_id,
    list_product_reviews,
)

router = APIRouter()


def _current_user_id(current_user: User | dict) -> int:
    if isinstance(current_user, dict):
        return int(current_user["id"])
    return int(current_user.id)


def _current_user_role(current_user: User | dict) -> str:
    if isinstance(current_user, dict):
        return str(current_user.get("role") or "")
    return str(current_user.role or "")


@router.get("")
def list_reviews(product_id: int = Query(...), db: Session = Depends(get_db)):
    return list_product_reviews(db, product_id)


@router.get("/products/{product_id}")
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    return list_product_reviews(db, product_id)


@router.post("/products/{product_id}")
def create_product_review(
    product_id: int,
    payload: dict = Body(default_factory=dict),
    current_user: User | dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if get_product(db, product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        rating = float(payload.get("rating"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="rating must be a number")
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")

    user_id = _current_user_id(current_user)
    if get_existing_review(db, product_id, user_id):
        raise HTTPException(
            status_code=409, detail="You have already reviewed this product"
        )

    review = create_review(
        db,
        product_id=product_id,
        user_id=user_id,
        rating=rating,
        comment=payload.get("comment") or payload.get("body"),
        image_url=payload.get("image_url"),
    )
    return review


@router.post("")
def create_review_route(
    payload: ReviewCreate,
    current_user: User | dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_product_review(
        product_id=payload.product_id,
        payload={
            "rating": payload.rating,
            "comment": getattr(payload, "body", None),
            "image_url": None,
        },
        current_user=current_user,
        db=db,
    )


@router.delete("/{review_id}")
def delete_review_route(
    review_id: int,
    current_user: User | dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = get_review_by_id(db, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    uid = _current_user_id(current_user)
    role = _current_user_role(current_user)
    if review.user_id != uid and role != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")
    return delete_review(db, review_id)
