from __future__ import annotations
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.promotions.ports import get_referral_config
from domains.customers.services.reviews_service import create_review, get_product_reviews, update_review, delete_review
from domains.customers.services.wishlist_service import (
    add_to_wishlist,
    remove_from_wishlist,
    get_user_wishlist as _get_user_wishlist,
)
from domains.customers.services.wishlist_write_service import clear_wishlist as _clear_wishlist



"""Admin customers router — canonical."""



router = APIRouter(prefix="/api/v1/admin/customers", tags=["admin", "customers"])


@router.get("/referrals/config", status_code=200, tags=["referrals"])
def get_referral_config_route(_: dict = Depends(require_admin), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.referral.manage"))
):
    return get_referral_config(db)


@router.get("/reviews/products/{product_id}", status_code=200, tags=["reviews"])
def get_product_reviews_route(
    product_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Query(50),
    cursor: Optional[int] = Query(None),
    _rf_gate: None = Depends(require_feature("customers.reviews.write")),
):
    return get_product_reviews(product_id=product_id, db=db, limit=limit, cursor=cursor)


@router.get("/reviews", status_code=200, tags=["reviews"])
def list_reviews_route(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    product_id: Optional[int] = Query(None),
    limit: int = Query(50),
    cursor: Optional[int] = Query(None),
    _rf_gate: None = Depends(require_feature("customers.reviews.write")),
):
    return get_product_reviews(product_id=product_id, db=db, limit=limit, cursor=cursor)


@router.put("/reviews/{review_id}", status_code=200, tags=["reviews"])
def update_review_route(
    review_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    review: dict = Body(...),
    _rf_gate: None = Depends(require_feature("customers.reviews.write")),
):
    return update_review(review_id=review_id, review_data=review, current_user=current_user, db=db)


@router.get("", status_code=200, tags=["wishlist"])
def get_wishlist_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = Query(200),
    cursor: Optional[int] = Query(None),
    _rf_gate: None = Depends(require_feature("customers.wishlist.manage")),
):
    user_id = current_user.get("user_id") or current_user.get("id")
    return _get_user_wishlist(db=db, user_id=user_id, limit=limit, cursor=cursor)


@router.post("/{product_id}", status_code=201, tags=["wishlist"])
def add_to_wishlist_route(
    product_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.wishlist.manage")),
):
    user_id = current_user.get("user_id") or current_user.get("id")
    return add_to_wishlist(user_id=user_id, product_id=product_id, db=db)


@router.delete("", status_code=200, tags=["wishlist"])
def clear_user_wishlist_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("customers.wishlist.manage")),
):
    user_id = current_user.get("user_id") or current_user.get("id")
    deleted = _clear_wishlist(db=db, user_id=user_id)
    return {"cleared": deleted}
