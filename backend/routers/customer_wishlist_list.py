"""Customer wishlist router (ROUTERS layer, flat file).

Thin HTTP layer: request parsing/validation, authentication, pagination query
params, and delegation to ``controllers.commerce.wishlist_controller``. No
direct DB/ORM access here; all persistence lives in the services layer.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from controllers.commerce.wishlist_controller import (
    add_to_wishlist as ctrl_add,
    clear_user_wishlist as ctrl_clear,
    get_wishlist as ctrl_get,
    remove_from_wishlist as ctrl_remove,
)
from utils.dependencies import get_current_user, get_db
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1")


def _user_id(current_user) -> int:
    if isinstance(current_user, dict):
        return int(current_user["id"])
    return int(current_user.id)


class WishlistItemOut(BaseModel):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[WishlistItemOut])
def list_wishlist(
    limit: int = Query(200, ge=1, le=200),
    cursor: Optional[int] = Query(None, description="WishlistItem id to paginate after"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ctrl_get(_user_id(current_user), db, limit=limit, cursor=cursor)


@router.post("/{product_id}", response_model=WishlistItemOut, status_code=201)
def add_wishlist_item(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ctrl_add(product_id, _user_id(current_user), db)


@router.delete("/{product_id}", response_model=dict)
def remove_wishlist_item(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ctrl_remove(product_id, _user_id(current_user), db)


@router.delete("", response_model=dict)
def clear_wishlist(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ctrl_clear(_user_id(current_user), db)
