"""Reviews router.

Thin HTTP layer: parses requests, enforces authentication, and delegates all
business logic to controllers.reviews_controller. No direct DB/ORM access here.
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from controllers.reviews_controller import (
    create_review as ctrl_create_review,
    delete_review as ctrl_delete_review,
    get_product_reviews as ctrl_get_product_reviews,
)
from utils.dependencies import get_current_user, get_db

router = APIRouter()


def _current_user_map(current_user) -> dict:
    if isinstance(current_user, dict):
        return current_user
    return {
        "id": int(current_user.id),
        "role": getattr(current_user, "role", None),
        "username": getattr(current_user, "username", None),
    }


@router.get("")
def list_reviews(product_id: int = Query(...), db: Session = Depends(get_db)):
    return ctrl_get_product_reviews(product_id, skip=0, limit=50, db=db)


@router.get("/products/{product_id}")
def get_product_reviews(product_id: int, db: Session = Depends(get_db)):
    return ctrl_get_product_reviews(product_id, skip=0, limit=50, db=db)


@router.post("/products/{product_id}")
def create_product_review(
    product_id: int,
    payload: dict = Body(default_factory=dict),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ctrl_create_review(product_id, payload, _current_user_map(current_user), db)


@router.post("")
def create_review(
    payload: dict = Body(default_factory=dict),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raw_product_id = payload.get("product_id")
    if raw_product_id is None:
        raise HTTPException(status_code=422, detail="product_id is required")
    return ctrl_create_review(int(raw_product_id), payload, _current_user_map(current_user), db)


@router.delete("/{review_id}")
def delete_review(review_id: int, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return ctrl_delete_review(review_id, _current_user_map(current_user), db)
