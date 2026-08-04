"""Wishlist router."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from controllers.products_controller import get_products as get_products_controller
from data.db import get_db
from data.models import User
from utils.dependencies import get_current_user
from utils.pagination import cursor_paginate_desc, build_cursor_pagination_payload

from services.catalog.products_write_service import (
    get_product_by_id,
    get_wishlist_item,
    list_wishlist_items,
    add_wishlist_item,
    remove_wishlist_item,
)

router = APIRouter()


def _product_exists_for_wishlist(product_id: int, db: Session) -> bool:
    if get_product_by_id(db, product_id) is not None:
        return True

    # Keep wishlist compatibility with IDs coming from the public /products feed,
    # even when a stale cache makes direct row lookup inconsistent.
    try:
        visible_products = get_products_controller(
            db=db,
            response=None,
            limit=500,
            offset=0,
        )
    except Exception:
        return False

    for entry in visible_products:
        candidate_id = entry.get("id") if isinstance(entry, dict) else getattr(entry, "id", None)
        if candidate_id == product_id:
            return True
    return False

@router.get("")
def get_wishlist(limit: int = 200, offset: int = 0, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_wishlist_items(db, int(current_user.get("id")), offset, limit)

@router.post("/{product_id}")
def add_to_wishlist(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if not _product_exists_for_wishlist(product_id, db):
        raise HTTPException(status_code=404, detail="Product not found")
    if get_wishlist_item(db, int(current_user.get("id")), product_id):
        return {"product_id": product_id, "detail": "Already in wishlist"}
    add_wishlist_item(db, int(current_user.get("id")), product_id)
    return {"product_id": product_id, "detail": "Added to wishlist"}

@router.delete("/{product_id}")
def remove_from_wishlist(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_wishlist_item(db, int(current_user.get("id")), product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    remove_wishlist_item(db, item)
    return {"product_id": product_id, "detail": "Removed from wishlist"}
