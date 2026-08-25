"""Admin customers router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .customers import router as customers_router
from .referrals import router as referrals_router
from .reviews import router as reviews_router
from __future__ import annotations
from domains.catalog.ports import list_reviews
from domains.customers.services.referrals.referrals_service import get_referral_code
from domains.customers.services.referrals.referrals_service import get_referral_config
from domains.customers.services.reviews_service import create_review
from domains.customers.services.reviews_service import get_product_reviews
from domains.customers.services.reviews_service import update_review
from domains.customers.services.wishlist_service import add_to_wishlist
from domains.customers.services.wishlist_service import remove_from_wishlist
from domains.customers.services.wishlist_service_from_accounts import get_wishlist
from domains.orders.services._auto_stubs import WishlistItemOut
from domains.orders.services._auto_stubs import clear_user_wishlist
from domains.orders.services._auto_stubs import get_review
from domains.orders.services.orders_package_service import delete_review
from infrastructure.database.database import get_db
from infrastructure.database.schemas import ReviewCreate
from infrastructure.database.schemas import ReviewOut
from infrastructure.utils.dependencies import get_current_user
from sqlalchemy.orm import Session
from typing import Any, Dict
from typing import List, Optional
import logging as _l; _l.getLogger(__name__).warning("skip customers_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip referrals_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip reviews_router: %s", _e)

router = APIRouter(prefix="/api/v1/admin/customers", tags=["admin", "customers"])

@router.get("/referrals/config", status_code=200, tags=['referrals'], summary="Get the active referral-program configuration")
def get_referral_config_route(
    db: Session = Depends(get_db)


@router.get("/referrals/code", status_code=200, tags=['referrals'], summary="Get or create the referral code for a user")
def get_referral_code_route(
    user_id: int = Query(None),
    db: Session = Depends(get_db)


@router.get("/reviews/products/{product_id}", response_model=List[ReviewOut], status_code=200, tags=['reviews'])
def get_product_reviews_route(
    product_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(50),
    cursor: Optional[int] = Query(None)


@router.get("/reviews", response_model=List[ReviewOut], status_code=200, tags=['reviews'])
def list_reviews_route(
    db: Session = Depends(get_db),
    product_id: Optional[int] = Query(None),
    limit: int = Query(50),
    cursor: Optional[int] = Query(None)


@router.get("/reviews/{review_id}", response_model=ReviewOut, status_code=200, tags=['reviews'])
def get_review_route(
    review_id: int,
    db: Session = Depends(get_db)


@router.post("/reviews/products/{product_id}", response_model=ReviewOut, status_code=201, tags=['reviews'])
def create_review_route(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    review: ReviewCreate = Body(...)


@router.put("/reviews/{review_id}", response_model=ReviewOut, status_code=200, tags=['reviews'])
def update_review_route(
    review_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    review: ReviewCreate = Body(...)


@router.delete("/reviews/{review_id}", response_model=ReviewOut, status_code=200, tags=['reviews'])
def delete_review_route(
    review_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.get("", response_model=List[WishlistItemOut], status_code=200, tags=['wishlist'])
def get_wishlist_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(200),
    cursor: Optional[int] = Query(None)


@router.post("/{product_id}", response_model=WishlistItemOut, status_code=201, tags=['wishlist'])
def add_to_wishlist_route(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.delete("/{product_id}", response_model=dict, status_code=200, tags=['wishlist'])
def remove_from_wishlist_route(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)


@router.delete("", response_model=dict, status_code=200, tags=['wishlist'])
def clear_user_wishlist_route(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)

