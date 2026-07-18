"""Reviews router."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import get_db
from models import Product, Review, User
from db.schemas import ReviewCreate
from utils.dependencies import get_current_user

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
    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .order_by(Review.created_at.desc())
        .all()
    )


@router.get("/products/{product_id}")
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.is_deleted == False)  # noqa: E712
        .order_by(Review.created_at.desc())
        .all()
    )


@router.post("/products/{product_id}")
def create_product_review(
    product_id: int,
    payload: dict = Body(default_factory=dict),
    current_user: User | dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.query(Product).filter(Product.id == product_id).first() is None:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        rating = float(payload.get("rating"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="rating must be a number")
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")

    user_id = _current_user_id(current_user)
    existing = (
        db.query(Review)
        .filter(
            Review.product_id == product_id,
            Review.user_id == user_id,
            Review.is_deleted == False,  # noqa: E712
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="You have already reviewed this product")

    review = Review(
        product_id=product_id,
        user_id=user_id,
        rating=rating,
        comment=payload.get("comment") or payload.get("body"),
        image_url=payload.get("image_url"),
        is_verified_purchase=False,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.post("")
def create_review(payload: ReviewCreate, current_user: User | dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_product_review(
        product_id=payload.product_id,
        payload={"rating": payload.rating, "comment": getattr(payload, "body", None), "image_url": None},
        current_user=current_user,
        db=db,
    )


@router.delete("/{review_id}")
def delete_review(review_id: int, current_user: User | dict = Depends(get_current_user), db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id, Review.is_deleted == False).first()  # noqa: E712
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != _current_user_id(current_user) and _current_user_role(current_user) != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")
    review.is_deleted = True
    db.commit()
    return {"detail": "Review deleted"}

