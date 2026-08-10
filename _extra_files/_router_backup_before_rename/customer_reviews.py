"""Customer reviews router (ROUTERS layer, flat file).

Thin HTTP layer: parses/validates requests, enforces authentication, and
delegates all business logic to controllers.commerce.reviews_controller. No
direct DB/ORM access here. All persistence lives in the services layer.
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from controllers.commerce.reviews_controller import (
    create_review as ctrl_create_review,
    delete_review as ctrl_delete_review,
    get_product_reviews as ctrl_get_product_reviews,
    get_review as ctrl_get_review,
    update_review as ctrl_update_review,
)
from data.db_schemas import ReviewCreate, ReviewOut
from utils.dependencies import get_current_user, get_db
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/products/{product_id}", response_model=list[ReviewOut])
def list_product_reviews(
    product_id: int,
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[int] = Query(None, description="Review id to paginate after"),
    db: Session = Depends(get_db),
):
    return ctrl_get_product_reviews(product_id, limit=limit, cursor=cursor, db=db)


@router.get("", response_model=list[ReviewOut])
def list_reviews(
    product_id: int = Query(..., description="Product id to fetch reviews for"),
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[int] = Query(None, description="Review id to paginate after"),
    db: Session = Depends(get_db),
):
    return ctrl_get_product_reviews(product_id, limit=limit, cursor=cursor, db=db)


@router.post("/products/{product_id}", response_model=ReviewOut, status_code=201)
def create_product_review(
    product_id: int,
    review: ReviewCreate = Body(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ctrl_create_review(product_id, review, current_user, db)


@router.get("/{review_id}", response_model=ReviewOut)
def get_single_review(review_id: int, db: Session = Depends(get_db)):
    return ctrl_get_review(review_id, db)


@router.put("/{review_id}", response_model=ReviewOut)
def update_product_review(
    review_id: int,
    review: ReviewCreate = Body(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ctrl_update_review(review_id, review, current_user, db)


@router.delete("/{review_id}", response_model=ReviewOut)
def delete_product_review(
    review_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ctrl_delete_review(review_id, current_user, db)
